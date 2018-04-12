import sys
import os
import re
import yaml
import pystache
import collections
import argparse

parser = argparse.ArgumentParser(description='Generate text based on Mustache extended templates.')
parser.add_argument('template', type=str, help='Path to template directory')
parser.add_argument('data', type=str, help='Path to data used to fill based on templates')
parser.add_argument('result', type=str, help='Path where the generate files or directories will be placed')

args = parser.parse_args()
template_path = args.template
data_path = args.data
result_path = args.result

def yaml_loader(path, context = {}):
    if os.path.isfile(path):
        partial_document = yaml.load(open(path, 'r'))
        if isinstance(context, list):
            context += [partial_document]
        else:
            context.update(partial_document)

        return context

    for resource in os.listdir(path):
        resource_path = os.path.join(path, resource)

        if os.path.isdir(resource_path):
            if isinstance(context, dict):
                if context.__contains__(resource) == False:
                    context[resource] = [] 
                yaml_loader(resource_path, context[resource])
            else:
                document = {}
                context += [document]
                yaml_loader(resource_path, document)
        else:
            yaml_loader(resource_path, context)

    return context

document = yaml_loader(data_path)
print('\nUsing data: ')
__import__('pprint').pprint(document)
print('\n')

mustache_pattern = re.compile(r'__([^_]+)__')

def mustache_directory_apply(path, context):
    for resource in os.listdir(path):
        resource_path = os.path.join(path, resource)
        extended_mustache_name = mustache_pattern.search(resource)
        if extended_mustache_name != None:
            mustache_name = extended_mustache_name.group(1) if extended_mustache_name != None else resource
            _, context = extended_mustache_solve_context(mustache_name, context)

        for context_item in (context if isinstance(context, list) else [context]):
            context = context_item
            generated_name = solve_extended_mustache(resource, context)
            generated_directory = mustache_path_apply(path.replace(template_path, result_path), document)
            generated_path = os.path.join(generated_directory, generated_name)

            if os.path.isfile(resource_path):
                print('[Generated file] \t%s' % generated_path)
                mustache_file_apply(resource_path, generated_path, context)
            else:
                print('[Created directory] \t%s' % generated_path)
                os.makedirs(generated_path)
                mustache_directory_apply(resource_path, context)

def mustache_path_apply(path, context):
    final_path = []
    for resource in path.split('/'):
        resource = solve_extended_mustache(resource, context)
        final_path.append(resource)

    return os.path.join(*final_path)

def solve_extended_mustache(resource, context):
    mustache_on_file = mustache_pattern.search(resource)
    last_context = None
    while mustache_on_file != None:
        extended_mustache_name = mustache_on_file.group(1)
        if extended_mustache_name != resource:
            key, last_context = extended_mustache_solve_context(extended_mustache_name, document)
            resource = resource.replace(mustache_on_file.group(), str(context[key]))
        mustache_on_file = mustache_pattern.search(resource)
    return resource 


def extended_mustache_solve_context(name, context):
    path = name.split('.')
    value = path[-1]
    path = path[:-1]
    for resource in path:
        context = context[resource]
    return value, context

def mustache_file_apply(template_path, generated_path, context):
    print('[Filling] \t\t' + template_path + ' => ' + generated_path)
    template_stream = open(template_path, 'r')
    template = template_stream.read()
    generated = pystache.render(template, context)
    generatade_file_stream = open(generated_path, 'w')
    generatade_file_stream.write(generated)

mustache_directory_apply(template_path, document)
