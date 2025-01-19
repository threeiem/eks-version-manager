#!/usr/bin/env python3

from boto3.session import Session
from botocore.exceptions import ClientError, EndpointConnectionError
from collections import defaultdict
import argparse
import subprocess
import json
import yaml
import sys
from packaging import version

def compare_versions(v1, v2):
    """Compare two Kubernetes versions"""
    try:
        ver1 = version.parse(v1)
        ver2 = version.parse(v2)
        return (ver1 > ver2) - (ver1 < ver2)
    except version.InvalidVersion:
        return 0

def get_fargate_pods(cluster_name, region):
    """Get Fargate pods using kubectl"""
    try:
        # Get pods with fargate node selector
        result = subprocess.run([
            'kubectl', 'get', 'pods',
            '--all-namespaces',
            '--field-selector', 'spec.nodeName!=',
            '-o', 'json'
        ], check=True, capture_output=True, text=True)
        
        pods = json.loads(result.stdout)
        fargate_pods = [pod for pod in pods['items'] 
                       if pod.get('spec', {}).get('schedulerName') == 'fargate-scheduler']
        return fargate_pods
    except subprocess.CalledProcessError as e:
        print(f"Error getting Fargate pods: {e}", file=sys.stderr)
        return []

def get_cluster_nodes(cluster_name, region):
    """Get the actual Kubernetes nodes using kubectl"""
    try:
        # Update kubeconfig for the cluster
        subprocess.run([
            'aws', 'eks', 'update-kubeconfig',
            '--name', cluster_name,
            '--region', region
        ], check=True, capture_output=True)
        
        # Get nodes using kubectl
        result = subprocess.run([
            'kubectl', 'get', 'nodes',
            '-o', 'json'
        ], check=True, capture_output=True, text=True)
        
        nodes = json.loads(result.stdout)
        return nodes['items']
    except subprocess.CalledProcessError as e:
        print(f"Error getting nodes: {e}", file=sys.stderr)
        return []

def check_version_filters(control_plane_version, node_versions, version_filters):
    """Check if cluster matches version filters"""
    if not version_filters:
        return True
        
    if version_filters.get('exact'):
        if control_plane_version != version_filters['exact']:
            return False
            
    if version_filters.get('min'):
        if compare_versions(control_plane_version, version_filters['min']) < 0:
            return False
            
    if version_filters.get('max'):
        if compare_versions(control_plane_version, version_filters['max']) > 0:
            return False
            
    if version_filters.get('outdated'):
        # Check for version mismatches between control plane and nodes
        if len(node_versions) > 1:  # Multiple node versions exist
            return True
        if node_versions and compare_versions(list(node_versions)[0], control_plane_version) != 0:
            return True
        return False
        
    return True

def get_all_eks_info(specific_region=None, specific_cluster=None, version_filters=None):
    session = Session()
    
    try:
        if specific_region:
            regions = [specific_region]
        else:
            ec2 = session.client('ec2')
            regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    except ClientError as e:
        print(f"Error getting AWS regions: {e.response['Error']['Message']}", file=sys.stderr)
        return {}
        
    result = {}
    for region in regions:
        result[region] = {"clusters": []}
        
        try:
            eks = session.client('eks', region_name=region)
            
            if specific_cluster:
                clusters = [specific_cluster]
            else:
                clusters = eks.list_clusters()['clusters']
            
            for cluster_name in clusters:
                try:
                    cluster = eks.describe_cluster(name=cluster_name)['cluster']
                    control_plane_version = cluster['version']
                    
                    # Get actual nodes and their versions
                    k8s_nodes = get_cluster_nodes(cluster_name, region)
                    node_versions = {node['status']['nodeInfo']['kubeletVersion'] for node in k8s_nodes}
                    
                    # Check version filters
                    if not check_version_filters(control_plane_version, node_versions, version_filters):
                        continue
                    
                    # Get Fargate pods
                    fargate_pods = get_fargate_pods(cluster_name, region)
                    
                    cluster_info = {
                        'name': cluster_name,
                        'control_plane': {
                            'version': control_plane_version,
                            'status': cluster['status'],
                            'platform_version': cluster.get('platformVersion', 'N/A'),
                            'endpoint': cluster['endpoint']
                        },
                        'tags': cluster.get('tags', {}),
                        'compute': {
                            'managed_nodegroups': [],
                            'nodes': [],
                            'fargate': {
                                'pods': []
                            }
                        }
                    }
                    
                    # Add Kubernetes node information
                    for node in k8s_nodes:
                        node_info = {
                            'name': node['metadata']['name'],
                            'status': node['status']['conditions'][-1]['type'],
                            'instance_type': node['metadata']['labels'].get('node.kubernetes.io/instance-type', 'N/A'),
                            'k8s_version': node['status']['nodeInfo']['kubeletVersion'],
                            'capacity': node['status'].get('capacity', {}),
                            'labels': node['metadata'].get('labels', {})
                        }
                        cluster_info['compute']['nodes'].append(node_info)
                    
                    # Add Fargate pod information
                    for pod in fargate_pods:
                        pod_info = {
                            'name': pod['metadata']['name'],
                            'namespace': pod['metadata']['namespace'],
                            'status': pod['status']['phase'],
                            'labels': pod['metadata'].get('labels', {})
                        }
                        cluster_info['compute']['fargate']['pods'].append(pod_info)
                    
                    # Check for EKS managed nodegroups
                    try:
                        nodegroup_response = eks.list_nodegroups(clusterName=cluster_name)
                        if 'nodegroups' in nodegroup_response and nodegroup_response['nodegroups']:
                            nodegroups = nodegroup_response['nodegroups']
                            for ng_name in nodegroups:
                                try:
                                    ng = eks.describe_nodegroup(
                                        clusterName=cluster_name,
                                        nodegroupName=ng_name
                                    )['nodegroup']
                                    
                                    nodegroup_info = {
                                        'name': ng_name,
                                        'status': ng['status'],
                                        'instance_types': ng['instanceTypes'],
                                        'ami_version': ng.get('amiVersion', 'N/A'),
                                        'k8s_version': ng.get('version', 'N/A'),
                                        'scaling': {
                                            'desired': ng['scalingConfig']['desiredSize'],
                                            'max': ng['scalingConfig']['maxSize'],
                                            'min': ng['scalingConfig']['minSize']
                                        },
                                        'tags': ng.get('tags', {})
                                    }
                                    
                                    cluster_info['compute']['managed_nodegroups'].append(nodegroup_info)
                                    
                                except ClientError as e:
                                    print(f"Error describing nodegroup {ng_name}: {e.response['Error']['Message']}", 
                                          file=sys.stderr)
                                
                    except ClientError as e:
                        print(f"Error listing nodegroups: {e.response['Error']['Message']}", file=sys.stderr)
                    
                    result[region]['clusters'].append(cluster_info)
                    
                except ClientError as e:
                    print(f"Error describing cluster {cluster_name}: {e.response['Error']['Message']}", 
                          file=sys.stderr)
                        
        except EndpointConnectionError:
            print(f"Unable to connect to region {region}", file=sys.stderr)
        except ClientError as e:
            print(f"Error accessing EKS in region {region}: {e.response['Error']['Message']}", 
                  file=sys.stderr)
            
    return result

def parse_args():
    parser = argparse.ArgumentParser(
        description='Get EKS cluster information across AWS regions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Show all clusters
  %(prog)s
  
  # Show clusters in specific region
  %(prog)s --region us-west-2
  
  # Show clusters running version 1.25 or newer
  %(prog)s --min-version 1.25
  
  # Show clusters with version mismatches
  %(prog)s --outdated
  
  # Output as YAML
  %(prog)s --yaml
        '''
    )
    
    parser.add_argument('--region', help='Specific AWS region to check')
    parser.add_argument('--cluster', help='Specific cluster name to check (requires --region)')
    
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('--json', action='store_true', help='Output in JSON format')
    output_group.add_argument('--yaml', action='store_true', help='Output in YAML format')
    
    version_group = parser.add_argument_group('version filtering')
    version_group.add_argument('--min-version', help='Show only clusters with version >= specified (e.g., 1.24)')
    version_group.add_argument('--max-version', help='Show only clusters with version <= specified (e.g., 1.27)')
    version_group.add_argument('--exact-version', help='Show only clusters matching exact version')
    version_group.add_argument('--outdated', action='store_true', 
                             help='Show only clusters where control plane and node versions mismatch')
    
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    if args.cluster and not args.region:
        parser.error('--cluster requires --region to be specified')
    
    return args

def main():
    args = parse_args()
    
    version_filters = {}
    if args.exact_version:
        version_filters['exact'] = args.exact_version
    if args.min_version:
        version_filters['min'] = args.min_version
    if args.max_version:
        version_filters['max'] = args.max_version
    if args.outdated:
        version_filters['outdated'] = True
    
    clusters = get_all_eks_info(args.region, args.cluster, version_filters)
    
    if args.json:
        print(json.dumps(clusters, indent=2))
        return
    elif args.yaml:
        print(yaml.dump(clusters, default_flow_style=False))
        return
        
    # Print human-readable summary
    for region, data in clusters.items():
        if not data['clusters']:
            if args.debug:
                print(f"\nNo matching clusters found in region: {region}")
            continue
            
        print(f"\nRegion: {region}")
        print(f"Number of clusters: {len(data['clusters'])}")
        
        for cluster in data['clusters']:
            print(f"\n  Cluster: {cluster['name']}")
            
            # Control plane info
            cp = cluster['control_plane']
            print(f"  Control Plane:")
            print(f"    Version: {cp['version']}")
            print(f"    Status: {cp['status']}")
            print(f"    Platform Version: {cp['platform_version']}")
            
            # Tags
            if cluster['tags']:
                print(f"\n  Tags:")
                for key, value in cluster['tags'].items():
                    print(f"    {key}: {value}")
            
            compute = cluster['compute']
            
            # Managed nodegroups
            if compute['managed_nodegroups']:
                print(f"\n  EKS Managed Nodegroups:")
                for ng in compute['managed_nodegroups']:
                    print(f"    - {ng['name']}:")
                    print(f"      Status: {ng['status']}")
                    print(f"      K8s Version: {ng['k8s_version']}")
                    print(f"      Instance Types: {', '.join(ng['instance_types'])}")
                    print(f"      Desired/Min/Max: {ng['scaling']['desired']}/{ng['scaling']['min']}/{ng['scaling']['max']}")
                    if ng['tags']:
                        print(f"      Tags:")
                        for key, value in ng['tags'].items():
                            print(f"        {key}: {value}")
            else:
                print("\n  No EKS managed nodegroups found")
                
            # Kubernetes nodes
            if compute['nodes']:
                print(f"\n  Kubernetes Nodes:")
                for node in compute['nodes']:
                    print(f"    - {node['name']}:")
                    print(f"      Status: {node['status']}")
                    print(f"      Instance Type: {node['instance_type']}")
                    print(f"      K8s Version: {node['k8s_version']}")
            else:
                print("\n  No Kubernetes nodes found")
                
            # Fargate pods
            if compute['fargate']['pods']:
                print(f"\n  Fargate Pods:")
                for pod in compute['fargate']['pods']:
                    print(f"    - {pod['name']} (namespace: {pod['namespace']}):")
                    print(f"      Status: {pod['status']}")
            else:
                print("\n  No Fargate pods found")

if __name__ == "__main__":
    main()
