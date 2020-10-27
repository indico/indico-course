import itertools
import os
import re
import xml.etree.ElementTree as etree

import click
import json
import markdown
import yaml
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


ALL_FILES = {"contentObjects.json", "articles.json", "blocks.json", "components.json"}


class LinkPattern(InlineProcessor):
    """An inline processor which removes relative links."""
    def handleMatch(self, m, data):
        if m.group(2).startswith('http'):
            return (None, None, None)
        text = m.group(1)
        el = etree.Element("span")
        el.text = text
        return el, m.start(0), m.end(0)


class LinkExtension(Extension):
    def extendMarkdown(self, md):
        # negative lookbehind on '!' to make sure we don't catch images by accident
        LINK_PATTERN = r'(?<!\!)\[([^\]]+)\]\(([^\)]+)\)'
        md.inlinePatterns.register(LinkPattern(LINK_PATTERN, md), 'link_sanitizer', 1000)


def _sanitize_name(name):
    return re.sub(r"[^a-zA-z0-9]", "-", name)


def _find_item(item_list, path):
    # leaf path exists directly in dictionary (e.g. 'Webcast/Recording')
    # (this is not a 2-node path, the / is part of the name)
    found = [e for e in item_list if path in e]
    if found:
        return found[0]

    # non-leaf path (e.g. 'Meetings/Introduction')
    parts = path.split("/", 1)
    try:
        found = [e for e in item_list if parts[0] in e][0]
    except IndexError:
        return None
    if len(parts) == 2:
        # non-leaf node
        return _find_item(found[parts[0]], parts[1])
    else:
        # leaf
        return found[parts[0]]


def _find_md_files(nav_list, path):
    item = _find_item(nav_list, path)
    if not item:
        return None
    return _find_strings(path, item)


def _find_strings(prefix, item):
    if isinstance(item, str):
        yield (prefix, item)
    elif isinstance(item, dict):
        for name, i in item.items():
            for n, i in _find_strings(name, i):
                yield (n, i)
    else:
        yield from itertools.chain.from_iterable(_find_strings(prefix, i) for i in item)


def patch_json(obj, fpath):
    cnt = []
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            cnt = json.load(f)
    cnt.append(obj)
    with open(fpath, "w") as f:
        json.dump(cnt, f, indent=4)


def make_content_obj(co_name, metadata):
    obj = {
        "_id": "co-" + co_name.replace(" ", "-"),
        "_parentId": "course",
        "_type": "page",
        "_classes": "",
        "_htmlClasses": "",
        "title": co_name,
        "displayTitle": co_name,
        "body": None,
        "pageBody": None,
        "instruction": None,
        "_graphic": None,
        "linkText": "View",
        "_pageLevelProgress": {
            "_isEnabled": True,
            "_showPageCompletion": False,
            "_excludeAssessments": False,
            "_isCompletionIndicatorEnabled": False,
        },
    }
    if metadata:
        obj["duration"] = metadata["duration"]
    return obj


def make_article(article_name, co_name):
    return {
        "_id": "a-" + _sanitize_name(article_name),
        "_parentId": "co-" + _sanitize_name(co_name),
        "_type": "article",
        "_classes": "",
        "title": None,
        "displayTitle": None,
        "body": "",
        "instruction": "",
    }


def make_block(idx, block_name, article_name):
    b_id = "b-" + _sanitize_name(block_name) + "-" + str(idx)
    return {
        "_id": b_id,
        "_parentId": "a-" + article_name.replace(" ", "-"),
        "_type": "block",
        "_classes": "",
        "title": b_id,
        "displayTitle": block_name,
        "body": "",
        "instruction": "",
        "_trackingId": idx,
    }


def make_component(idx, block_name):
    suf = _sanitize_name(block_name) + "-" + str(idx)
    c_id = "c-" + suf
    b_id = f"b-{suf}"
    return {
        "_id": c_id,
        "_parentId": b_id,
        "_type": "component",
        "_component": "text",
        "_classes": "",
        "_layout": "full",
        "title": block_name,
        "displayTitle": None,
        "instruction": None,
        "_pageLevelProgress": {"_isEnabled": True},
    }


def make_question_component(idx, block_id, data):
    q_id = f"q-{block_id}-{idx}"
    return {
        "_id": q_id,
        "_parentId": block_id,
        "_type": "component",
        "_component": "mcq",
        "_classes": "",
        "_attempts": 1,
        "_questionWeight": 1,
        "_canShowModelAnswer": True,
        "_shouldDisplayAttempts": False,
        "_isRandom": True,
        "_selectable": data.get("num_selections", 1),
        "_layout": "full",
        "title": f"Question {idx}",
        "displayTitle": f"Question {idx}",
        "body": data["body"],
        "instruction": "Choose one option"
        if data.get("num_selections", 1) == 1
        else f"Choose {data['num_selections']} options",
        "_items": [
            {"text": item["text"], "_shouldBeSelected": item.get("correct", False)}
            for item in data["items"]
        ],
        "_feedback": {
            "title": "Feedback",
            "correct": "That’s correct!",
            "_incorrect": {"final": data["correction"]},
        },
        "_pageLevelProgress": {
            "_isEnabled": True,
            "_isCompletionIndicatorEnabled": True,
        },
    }


def create_content_object(adapt_dir, md_dir, co_name, metadata):
    output_dir = os.path.join(adapt_dir, "src", "course", "en")
    os.makedirs(output_dir, exist_ok=True)
    co_file = os.path.join(output_dir, "contentObjects.json")
    article_file = os.path.join(output_dir, "articles.json")
    block_file = os.path.join(output_dir, "blocks.json")
    component_file = os.path.join(output_dir, "components.json")
    md_yaml = yaml.load(
        open(os.path.join(md_dir, "mkdocs.yml")), Loader=yaml.SafeLoader
    )

    cur_bid = 1
    blocks = []
    if os.path.exists(block_file):
        with open(block_file, "r") as f:
            blocks = json.load(f)
            if blocks:
                cur_bid = blocks[-1]["_trackingId"] + 1

    click.echo(click.style("\U0001f4e6 Adding content object: " + co_name, fg="green"))
    patch_json(make_content_obj(co_name, metadata), co_file)

    article_name = co_name
    click.echo(click.style("\U0001f4dd Adding article: " + article_name, fg="green"))
    patch_json(make_article(article_name, co_name), article_file)

    md_content = {}
    contents = metadata.get("contents")
    files = contents.get("files")
    if files:
        for name in files:
            md_files = _find_md_files(md_yaml["nav"], name)
            if not md_files:
                click.echo(click.style(f"Couldn't find {name}", fg="red"), err=True)
                continue
            for block_name, rel_path in md_files:
                path = os.path.join(md_dir, "docs", rel_path)
                with open(path, "r") as f:
                    md_content[block_name] = f.read()
    else:
        md = contents.get("markdown")
        if not md:
            raise Exception(f"Section {co_name} has no contents")
        for block in md:
            md_content[block["title"]] = block["content"]

    for block_name, md_block in md_content.items():
        click.echo(click.style("\U0001f36a Adding block: " + block_name, fg="green"))
        md_block = md_block.replace("../assets/", "course/en/images/docs/")
        block_lines = md_block.strip().split("\n")
        first_line = block_lines[0].strip()
        if first_line.startswith("# "):
            md_block = "\n".join(block_lines[1:]).strip()
        patch_json(make_block(cur_bid, block_name, article_name), block_file)

        component = make_component(cur_bid, block_name)
        component["body"] = markdown.markdown(md_block, extensions=["admonition", "__main__:LinkExtension"])
        patch_json(component, component_file)

        cur_bid += 1

    questions = metadata.get("quiz", [])

    if not questions:
        return

    quiz = make_block(cur_bid + 1, f"{co_name} - Quizzes", article_name)
    patch_json(quiz, block_file)

    for n, question in enumerate(questions, 1):
        question = make_question_component(n, quiz["_id"], question)
        patch_json(question, component_file)


@click.command()
@click.argument("course_file", type=click.File("r"))
@click.argument("md_dir", type=click.Path(exists=True))
@click.argument("adapt_dir", type=click.Path(exists=True))
@click.option("-r", "--replace", is_flag=True, help="Replace existing contents")
def md_to_adapt(course_file, md_dir, adapt_dir, replace):
    if replace:
        for file_name in ALL_FILES:
            path = os.path.join(adapt_dir, "src", "course", "en", file_name)
            if os.path.exists(path):
                os.unlink(path)

    data_yaml = yaml.load(course_file, Loader=yaml.SafeLoader)

    for co_name, metadata in data_yaml.items():
        create_content_object(adapt_dir, md_dir, co_name, metadata)


if __name__ == "__main__":
    md_to_adapt()
