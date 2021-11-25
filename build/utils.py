def make_header_id(tag_text):
    return tag_text.lower().replace(' ', '-')


def wrap_unwrap_fake_tag(text, wrap=True): # todo use lxml.html
    TAG_OPEN = '<FAKETAG>'
    TAG_CLOSE = '</FAKETAG>'

    if wrap:
        text = TAG_OPEN + text + TAG_CLOSE
    else:
        text = text[len(TAG_OPEN):][:-len(TAG_CLOSE)]
    return text