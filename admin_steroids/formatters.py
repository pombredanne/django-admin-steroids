import re

from django.core import urlresolvers
from django.utils.safestring import SafeString, mark_safe
from django.conf import settings

import utils

NONE_STR = '(None)'

class AdminFieldFormatter(object):
    """
    Base class for controlling the display formatting of field values
    in Django's admin.
    """
    
    # Only necessary for logic in admin.helpers.AdminReadonlyField.__init__.
    __name__ = 'AdminFieldFormatter'
    
    is_readonly = True
    
    object_level = False
    
    title_align = None
    
    null = False
    
    def __init__(self, name, title=None, **kwargs):
        self.name = name
        self.short_description = kwargs.get('short_description', title or name)
        kwargs.setdefault('allow_tags', True)
        kwargs.setdefault('admin_order_field', name)
        kwargs.setdefault('title_align',
            kwargs.get('align', kwargs.get('title_align')))
        self.__dict__.update(kwargs)
        
        if not isinstance(self.short_description, SafeString):
            self.short_description = re.sub(
                '[^0-9a-zA-Z]+',
                ' ',
                self.short_description).capitalize()
            
            #TODO: Allow markup in short_description? Not practical due to
            #hardcoded escape() in django.contrib.admin.helpers.AdminReadonlyField
#            if self.title_align:
#                title_template = '<span style="text-align:%s">%s</span>'
#                self.short_description = title_template \
#                    % (self.title_align, self.short_description)
#                self.short_description = mark_safe(self.short_description)
        
    def __call__(self, obj):
        if self.object_level:
            v = obj
        else:
            v = getattr(obj, self.name)
        if v is None and self.null:
            return NONE_STR
        return self.format(v)

class DollarFormat(AdminFieldFormatter):
    """
    Formats a numeric value as dollars.
    """
    
    decimals = 2
    
    title_align = 'right'
    
    align = 'right'
    
    commas = True
    
    def format(self, v):
        template = '$%.' + str(self.decimals) + 'f'
        if v < 0:
            v *= -1
            template = '('+template+')'
        if self.commas:
            template = utils.FormatWithCommas(template, v)
        else:
            template = template % v
        style = 'display:inline-block; width:100%%; text-align:'+self.align+';'
        template = '<span style="'+style+'">'+template+'</span>'
        return template

class PercentFormat(AdminFieldFormatter):
    """
    Formats a ratio as a percent.
    """
    
    template = '%.0f%%'
    
    align = 'right'
    
    def format(self, v):
        v *= 100
        template = self.template
        style = 'display:inline-block; width:100%%; text-align:'+self.align+';'
        template = '<span style="'+style+'">'+template+'</span>'
        return template % v
    
class CenterFormat(AdminFieldFormatter):
    """
    Formats a ratio as a percent.
    """
    
    title_align = 'center'
    
    align = 'center'
    
    def format(self, v):
        style = 'display:inline-block; width:100%%; text-align:'+self.align+';'
        template = '<span style="'+style+'">%s</span>'
        return template % v

class NbspFormat(AdminFieldFormatter):
    """
    Replaces all spaces with a non-breaking space.
    """
    
    def format(self, v):
        v = str(v)
        v = v.replace(' ', '&nbsp;')
        return v

class BooleanFormat(AdminFieldFormatter):
    """
    Converts the field value into a green checkmark image for true and red dash
    image false.
    """
    
    align = 'left'
    
    yes_path = '%sadmin/img/icon-yes.gif'
    
    no_path = '%sadmin/img/icon-no.gif'
    
    def format(self, v):
        v = bool(v)
        style = 'display:inline-block; width:100%%; text-align:'+self.align+';'
        template = '<span style="'+style+'"><img src="%s" alt="%s" title="%s" /></span>'
        if v:
            url = self.yes_path
        else:
            url = self.no_path
        url = url % (settings.MEDIA_URL,)
        v = template % (url, v, v)
        return v
    
class AdminOneToManyLink(AdminFieldFormatter):
    #TODO
    
    object_level = True
    
    url_param = None
    
    id_param = 'id'
    
    target = '_blank'
    
    def format(self, obj):
        try:
            
            url = urlresolvers.reverse(self.url_param)
            url = '{0}?{1}={2}'.format(url, self.id_param, obj.id)
            
            q = count = getattr(obj, self.name)
            if hasattr(q, 'count'):
                q = q.all()
                count = q.count()
                if count == 1:
                    # Link directly to the record if only one result.
                    link_obj = q[0]
                    url = utils.get_admin_change_url(link_obj)
            if count is None or count == 0:
                return count
            return '<a href="%s" target="%s"><input type="button" value="View %d" /></a>' % (url, self.target, count)
        except Exception, e:
            return str(e)