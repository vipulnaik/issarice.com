#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, Issa Rice
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import glob
import json
from jinja2 import Template, Environment, FileSystemLoader
import os

import commands as c
import metadata as meta
from classes import *
from tag_ontology import *

SITE_DIR = "_site/"
# relative to SITE_DIR
TAGS_DIR = "tags/"

pages_pat = "pages/*.md"
pages_lst = [Filepath(i) for i in glob.glob(pages_pat)]

def clean():
    print("Cleaning existing files")
    c.run_command("rm -rf dir".format(dir=SITE_DIR))
clean()

# Copy css
def copy_css():
    print("Copying CSS")
    if not os.path.exists(SITE_DIR + "css/"):
        os.makedirs(SITE_DIR + "css/")
    with open('css/minimal.css', 'r') as i, open(SITE_DIR + 'css/minimal.css', 'w') as o:
        x = i.read()
        o.write(x)
copy_css()

# Copy images
def copy_images():
    print("Copying images")
    for f in glob.glob("images/*"):
        c.run_command("cp {f} {to}".format(f=f, to=SITE_DIR))
copy_images()

# Copy static files
def copy_static():
    print("Copying static files")
    if not os.path.exists(SITE_DIR + "static/"):
        os.makedirs(SITE_DIR + "static/")
    for f in glob.glob("static/*"):
        c.run_command("cp {f} {to}".format(f=f, to=SITE_DIR + "static/"))
copy_static()

all_tags = []
page_data = []

# Make page for each page
for page_path in pages_lst:
    page = Page(page_path)
    print("Processing " + str(page.origin))
    page.load()
    page.json = meta.organize_tags(page.json, tag_synonyms, tag_implications)
    page.metadata.update_with(meta.get_metadata_dict(page.json))
    tags_lst = page.metadata.tags
    all_tags.extend(tags_lst)
    body = to_unicode(c.run_command("pandoc -f json -t html --toc --toc-depth=4 --template=templates/toc.html --smart --mathjax --base-header-level=2", pipe_in=json.dumps(page.json, separators=(',',':'))))

    inter = page.origin.route_with(set_extension("")).route_with(drop_one_parent_dir_route).path
    write_to = page.origin.route_with(my_route)

    ctxp = Metadata(
        tags = tags_lst,
        css = Filepath("css/minimal.css").relative_to(Filepath(inter)).path,
        source = page.origin.path,
    )
    ctx = Metadata(**default_metadata.__dict__)
    ctx.update_with(page.metadata)
    ctx.update_with(ctxp)

    env = Environment(loader=FileSystemLoader('.'))
    skeleton = env.get_template('templates/skeleton.html')
    tags = []
    for tag in ctx.tags:
        tags.append({'name': tag, 'path': to_unicode(Filepath(to_string(tag)).route_with(to_dir(TAGS_DIR)).path)})
    tags = sorted(tags, key=lambda t: t['name'])
    final = skeleton.render(body=body, page=ctx, tags=tags, css=ctx.css, path="./")
    page_data.append((ctx.title, inter, tags_lst)) # to be used later

    if not os.path.exists(SITE_DIR):
        os.makedirs(SITE_DIR)

    with open(write_to.path, 'w') as f:
        f.write(to_string(final))

all_tags = list(set(all_tags))

for tag in all_tags:
    print("Processing tag page for " + tag)
    pages = []
    for page_tuple in page_data:
        if tag in page_tuple[2]:
            pages.append({'title': to_unicode(page_tuple[0]), 'url': to_unicode("../" + page_tuple[1])})
    pages = sorted(pages, key=lambda t: t['title'])
    write_to = Filepath(SITE_DIR + TAGS_DIR + to_string(tag))
    ctx = Metadata(
        title = "Tag: " + tag,
        css = Filepath("css/minimal.css").relative_to(Filepath(TAGS_DIR + to_string(tag))).path,
        license = "cc0",
    )
    env = Environment(loader=FileSystemLoader('.'))
    page_list = env.get_template('templates/page-list.html')
    body = to_unicode(page_list.render(pages=pages))
    skeleton = env.get_template('templates/skeleton.html')
    final = skeleton.render(body=body, page=ctx, css=ctx.css, path="../")
    if not os.path.exists(SITE_DIR + TAGS_DIR):
        os.makedirs(SITE_DIR + TAGS_DIR)
    with open(write_to.path, 'w') as f:
        f.write(to_string(final))

# Make page with all tags
def create_page_with_all_tags():
    global all_tags
    print("Creating page with all the tags")
    env = Environment(loader=FileSystemLoader('.'))
    page_list = env.get_template('templates/page-list.html')
    pages = [{'title': to_unicode(tag), 'url': to_unicode(tag)} for tag in all_tags]
    pages = sorted(pages, key=lambda t: t['title'])
    body = to_unicode(page_list.render(pages=pages))
    skeleton = env.get_template('templates/skeleton.html')
    ctx = Metadata(
        title = "All tags",
        css = Filepath("css/minimal.css").relative_to(Filepath(TAGS_DIR + "index")).path,
        license = "cc0",
    )
    final = skeleton.render(page=ctx, body=body, css=ctx.css, path="./")
    if not os.path.exists(SITE_DIR + TAGS_DIR):
        os.makedirs(SITE_DIR + TAGS_DIR)
    with open(SITE_DIR + TAGS_DIR + "index", 'w') as f:
        f.write(to_string(final))

create_page_with_all_tags()

# Make page with all pages
def create_page_with_all_pages():
    global page_data
    print("Creating page with all the pages")
    env = Environment(loader=FileSystemLoader('.'))
    page_list = env.get_template('templates/page-list.html')
    pages = [{'title': to_unicode(page_tup[0]), 'url': to_unicode(page_tup[1])} for page_tup in page_data]
    pages = sorted(pages, key=lambda t: t['title'])
    body = page_list.render(pages=pages)
    skeleton = env.get_template('templates/skeleton.html')
    ctx = Metadata(
        title = "All pages on the site",
        css = Filepath("css/minimal.css").relative_to(Filepath("all")).path,
        license = "cc0",
    )
    final = skeleton.render(page=ctx, body=body, css=ctx.css, path="../")
    if not os.path.exists(SITE_DIR):
        os.makedirs(SITE_DIR)
    with open(SITE_DIR + "all", 'w') as f:
        f.write(to_string(final))
create_page_with_all_pages()
