from django import template
import json

register = template.Library()

@register.filter(name='jsonify')
def jsonify(obj):
    return json.dumps(obj) 