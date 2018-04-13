import sys
import os
import re
import yaml
import pystache
import collections
import argparse
import copy

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


mustache_pattern = re.compile(r'__([^_]+)__')

def mustache_directory_apply(path, context, directory):
    for resource in os.listdir(path):
        resource_path = os.path.join(path, resource)
        extended_mustache_name = mustache_pattern.search(resource)
        if extended_mustache_name != None:
            mustache_name = extended_mustache_name.group(1) if extended_mustache_name != None else resource
            key, new_context = extended_mustache_solve_context(mustache_name, context)
            resource = resource.replace(extended_mustache_name.group(), '__' + key + '__')
        else:
            new_context = copy.deepcopy(context)

        for context_item in (new_context if isinstance(new_context, list) else [new_context]):
            context_item = context_item
            generated_name = solve_extended_mustache(resource, context_item)
            generated_path = os.path.join(directory, generated_name)

            if os.path.isfile(resource_path):
                print('[Generated file] \t%s' % generated_path)
                mustache_file_apply(resource_path, generated_path, context_item)
            else:
                print('[Created directory] \t%s' % generated_path)
                os.makedirs(generated_path)
                new_directory = os.path.join(directory, generated_name)
                mustache_directory_apply(resource_path, context_item, new_directory)


def mustache_path_apply(path, context):
    final_path = []
    for resource in path.split('/'):
        resource = solve_extended_mustache(resource, context)
        final_path.append(resource)

    return os.path.join(*final_path)


def solve_extended_mustache(resource, context):
    context = copy.deepcopy(context)
    mustache_on_file = mustache_pattern.search(resource)
    while mustache_on_file != None:
        extended_mustache_name = mustache_on_file.group(1)
        if extended_mustache_name != resource:
            key, _ = extended_mustache_solve_context(extended_mustache_name, document)
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


def flat_globalize(context, global_context = dict(), prefix = ''):
    if isinstance(context, dict):
        for k, v in context.items():
            global_context[prefix + '.' + k] = v

        for k, v in context.items():
            flat_globalize(v, global_context, prefix + '.' + k)

    if isinstance(context, list):
        for item in context:
            flat_globalize(item, global_context, prefix)
            item.update(global_context)


def mustache_file_apply(template_path, generated_path, context):
    print('[Filling] \t\t' + template_path + ' => ' + generated_path)
    template_stream = open(template_path, 'r')
    template = template_stream.read()
    generated = pystache.render(template, context)
    generatade_file_stream = open(generated_path, 'w')
    generatade_file_stream.write(generated)

parser = argparse.ArgumentParser(description='Generate text based on Mustache extended templates.')
parser.add_argument('template', type=str, help='Path to template directory')
parser.add_argument('data', type=str, help='Path to data used to fill based on templates')
parser.add_argument('result', type=str, help='Path where the generate files or directories will be placed')

args = parser.parse_args()
template_path = args.template
data_path = args.data
result_path = args.result

document = yaml_loader(data_path)
print('\nUsing data: ')
__import__('pprint').pprint(document)
print('\n')

flat_globalize(document)

print('\nUsing globalized data: ')
__import__('pprint').pprint(document)
print('\n')

mustache_directory_apply(template_path, document, result_path)
