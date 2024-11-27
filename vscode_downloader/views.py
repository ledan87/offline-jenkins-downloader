from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import zipfile
import requests
import semver
from io import BytesIO
from .models import VsixPackage

def extension_list(request):
    # Example extensions data - you can replace this with your actual data
    extensions = [
        {
            'id': 'ms-python.python',
            'name': 'Python',
            'description': 'IntelliSense (Pylance), Linting, Debugging, code formatting, refactoring, etc.'
        },
        {
            'id': 'njpwerner.autodocstring',
            'name': 'autoDocstring',
            'description': 'Generates python docstrings automatically'
        },
        # Add more extensions as needed
    ]
    
    return render(request, 'vscode_downloader/main.html', {'extensions': extensions})

def download_extensions(request):
    if request.method == 'POST':
        selected_extensions = request.POST.getlist('selected_extensions')
        # TODO: Implement the download logic
        # This will be implemented in the next step
        pass



def browse_extensions(request):
    # Get query parameters with defaults
    page_size = int(request.GET.get('page_size', 20))
    max_page = int(request.GET.get('max_page', 1))
    search_query = request.GET.get('search', '')
    
    # Get extensions using the existing method
    extensions_list = []
    try:
        for extension in get_vscode_extensions(search_query=search_query, max_page=max_page, page_size=page_size):
            ext_data = {
                'displayName': extension.get('displayName', ''),
                'publisher': extension.get('publisher', {}).get('publisherName', ''),
                'publisherDisplayName': extension.get('publisher', {}).get('displayName', ''),
                'extensionName': extension.get('extensionName', ''),
                'shortDescription': extension.get('shortDescription', ''),
                'version': extension.get('versions', [{}])[0].get('version', ''),
            }
            extensions_list.append(ext_data)
    except Exception as e:
        return render(request, 'vscode_downloader/browse_extensions.html', {'error': str(e)})

    return render(request, 'vscode_downloader/browse_extensions.html', {
        'extensions': extensions_list,
        'search_query': search_query,
        'page_size': page_size,
        'max_page': max_page,
    })

def get_extension_details(request):
    extension_id = request.GET.get('extension_id', '')
    if not extension_id:
        return HttpResponse('Extension ID is required', status=400)
    
    try:
        extension_details = list(get_vscode_extensions(extensionId=extension_id, max_page=1))
        if not extension_details:
            return HttpResponse('Extension not found', status=404)
        
        # Process version compatibility information
        extension = extension_details[0]
        version_info = []
        
        for version in extension.get('versions', []):
            manifest_file = next(
                (file for file in version.get('files', [])
                 if file.get('assetType') == 'Microsoft.VisualStudio.Code.Manifest'),
                None
            )
            
            if manifest_file and manifest_file.get('source'):
                try:
                    # Fetch the manifest content
                    manifest_response = requests.get(manifest_file['source'])
                    manifest_response.raise_for_status()  # Raise exception for bad status codes
                    
                    manifest = manifest_response.json()
                    min_vscode = manifest.get('engines', {}).get('vscode', 'N/A')
                    version_info.append({
                        'version': version.get('version'),
                        'min_vscode': min_vscode.replace('^', '').replace('>=', '')  # Clean up version string
                    })
                except requests.RequestException as e:
                    version_info.append({
                        'version': version.get('version'),
                        'min_vscode': f'Error fetching manifest: {str(e)}'
                    })
                except json.JSONDecodeError:
                    version_info.append({
                        'version': version.get('version'),
                        'min_vscode': 'Error parsing manifest'
                    })
            else:
                version_info.append({
                    'version': version.get('version'),
                    'min_vscode': 'No manifest found'
                })
        
        extension_details[0]['version_info'] = version_info
            
        return render(request, 'vscode_downloader/extension_details.html', {
            'extension_details': extension_details
        })
    except Exception as e:
        return HttpResponse(f'Error fetching extension details: {str(e)}', status=500)


def get_vscode_extensions(search_query=None, extensionId=None, max_page=10000, page_size=100,
                          include_versions=True, include_files=True, include_category_and_tags=True, include_shared_accounts=True, include_version_properties=True,
                          exclude_non_validated=False, include_installation_targets=True, include_asset_uri=True, include_statistics=True,
                          include_latest_version_only=False, unpublished=False, include_name_conflict_info=True, api_version='7.2-preview.1', session=None):
    if not session:
        session = requests.session()

    headers = {'Accept': f'application/json; charset=utf-8; api-version={api_version}'}

    flags = 0
    if include_versions:
        flags |= 0x1

    if include_files:
        flags |= 0x2

    if include_category_and_tags:
        flags |= 0x4

    if include_shared_accounts:
        flags |= 0x8

    if include_shared_accounts:
        flags |= 0x8

    if include_version_properties:
        flags |= 0x10

    if exclude_non_validated:
        flags |= 0x20

    if include_installation_targets:
        flags |= 0x40

    if include_asset_uri:
        flags |= 0x80

    if include_statistics:
        flags |= 0x100

    if include_latest_version_only:
        flags |= 0x200

    if unpublished:
        flags |= 0x1000

    if include_name_conflict_info:
        flags |= 0x8000

    for page in range(1, max_page + 1):
        # Create base criteria list
        criteria = [
            {
                "filterType": 8,
                "value": "Microsoft.VisualStudio.Code"
            }
        ]
        
        # Add search filter if search_query is provided
        if search_query:
            criteria.append({
                "filterType": 10,
                "value": search_query
            })

        if extensionId:
            criteria.append({
                "filterType": 7,
                "value": extensionId
            })

        body = {
            "filters": [
                {
                    "criteria": criteria,
                    "pageNumber": page,
                    "pageSize": page_size,
                    "sortBy": 0,
                    "sortOrder": 0
                }
            ],
            "assetTypes": [],
            "flags": flags
        }

        r = session.post('https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery', json=body, headers=headers)
        r.raise_for_status()
        response = r.json()

        extensions = response['results'][0]['extensions']
        for extension in extensions:
            yield extension

        if len(extensions) != page_size:
            break



@csrf_exempt
@require_http_methods(["POST"])
def api_download_extensions(request):
    try:
        data = json.loads(request.body)
        extensions = data.get('extensions', [])
        vscode_version = data.get('vscodeVersion')
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for extension_data in extensions:
                # Get extension details to find compatible version
                extension_details = list(get_vscode_extensions(
                    extensionId=f"{extension_data['publisher']}.{extension_data['extension']}",
                    max_page=1
                ))
                
                if not extension_details:
                    continue
                    
                # Find the highest version compatible with vscode_version
                compatible_version = None
                for version in extension_details[0].get('versions', []):
                    manifest_file = next(
                        (file for file in version.get('files', [])
                         if file.get('assetType') == 'Microsoft.VisualStudio.Code.Manifest'),
                        None
                    )
                    
                    if manifest_file and manifest_file.get('source'):
                        try:
                            manifest_response = requests.get(manifest_file['source'])
                            manifest = manifest_response.json()
                            min_vscode = manifest.get('engines', {}).get('vscode', '')
                            min_version = min_vscode.replace('^', '').replace('>=', '')
                            
                            if semver.compare(vscode_version, min_version) >= 0:
                                compatible_version = version.get('version')
                                break
                        except:
                            continue
                
                if compatible_version:
                    vsix = VsixPackage(
                        publisher=extension_data['publisher'],
                        extension=extension_data['extension'],
                        version=compatible_version
                    )
                    
                    response = requests.get(vsix.get_url())
                    if response.status_code == 200:
                        zip_file.writestr(vsix.get_vsix_name(), response.content)
        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="vscode_extensions.zip"'
        return response
        
    except Exception as e:
        return HttpResponse(str(e), status=500)

def api_extension_details(request, extension_id):
    try:
        extension_details = list(get_vscode_extensions(extensionId=extension_id, max_page=1))
        if not extension_details:
            return JsonResponse({'error': 'Extension not found'}, status=404)
        
        extension = extension_details[0]
        version_info = []
        
        for version in extension.get('versions', []):
            manifest_file = next(
                (file for file in version.get('files', [])
                 if file.get('assetType') == 'Microsoft.VisualStudio.Code.Manifest'),
                None
            )
            
            if manifest_file and manifest_file.get('source'):
                try:
                    manifest_response = requests.get(manifest_file['source'])
                    manifest_response.raise_for_status()
                    
                    manifest = manifest_response.json()
                    min_vscode = manifest.get('engines', {}).get('vscode', 'N/A')
                    version_info.append({
                        'version': version.get('version'),
                        'min_vscode': min_vscode.replace('^', '').replace('>=', '')
                    })
                except (requests.RequestException, json.JSONDecodeError) as e:
                    version_info.append({
                        'version': version.get('version'),
                        'min_vscode': f'Error: {str(e)}'
                    })
            else:
                version_info.append({
                    'version': version.get('version'),
                    'min_vscode': 'No manifest found'
                })
        
        extension['version_info'] = version_info
        return JsonResponse(extension)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_compatible_version(extension_id, vscode_target_version):
    """
    Get the highest compatible version of an extension for a specific VSCode version.
    """
    try:
        extension_details = list(get_vscode_extensions(extensionId=extension_id, max_page=1))
        if not extension_details:
            return None
        
        extension = extension_details[0]
        # Sort versions by version number (newest first)
        versions = sorted(
            extension.get('versions', []),
            key=lambda x: x.get('version', '0.0.0'),
            reverse=True
        )
        
        for version in versions:
            manifest_file = next(
                (file for file in version.get('files', [])
                 if file.get('assetType') == 'Microsoft.VisualStudio.Code.Manifest'),
                None
            )
            
            if manifest_file and manifest_file.get('source'):
                try:
                    manifest_response = requests.get(manifest_file['source'])
                    manifest_response.raise_for_status()
                    
                    manifest = manifest_response.json()
                    min_vscode = manifest.get('engines', {}).get('vscode', 'N/A')
                    min_version = min_vscode.replace('^', '').replace('>=', '')

                    if semver.compare(vscode_target_version, min_version) >= 0:
                        return {
                            'version': version.get('version'),
                            'min_vscode': min_version
                        }
                except:
                    continue
        
        return None
    except Exception as e:
        return None

def api_get_compatible_version(request, extension_id, vscode_target_version):
    """API endpoint to get compatible version"""
    try:
        result = api_compatible_version(extension_id, vscode_target_version)
        if result:
            return JsonResponse(result)
        return JsonResponse({'error': 'No compatible version found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
