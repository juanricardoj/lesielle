# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
#
##############################################################################

from urllib.parse import quote

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    @api.model
    def sync_categories(self, category_obj, instance_id, channel, connection):
        if category_obj:
            mapped_category_objs = category_obj.connector_mapping_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
            if not mapped_category_objs:
                parent_categ_id = self.sync_categories(category_obj.parent_id, instance_id, channel, connection) if category_obj.parent_id else 1
                resp_translation = self.translationlang_sync(category_obj,instance_id) 
                if hasattr(self, 'create_%s_category' % channel):
                    name = category_obj.name
                    odoo_id = category_obj.id
                    response = getattr(self, 'create_%s_category' % channel)(odoo_id, parent_categ_id, name, connection)
                    if response.get('status', False):
                        ecomm_id = response.get('ecomm_id', 0)
                        if ecomm_id:
                            self.create_odoo_connector_mapping('connector.category.mapping', ecomm_id, odoo_id, instance_id)
                            self.create_ecomm_connector_mapping('connector.category.mapping', channel, {'ecomm_id':ecomm_id, 'odoo_id':odoo_id, 'created_by': 'odoo'}, connection)
                        return ecomm_id
            else:
                return mapped_category_objs[0].ecomm_id
        return False
    
    def translationlang_sync(self,categ_obj,instance_id):
        ctx = dict(self._context or {})
        response = False
        if ctx.get('translation_sync'):
            lang = ''
            if 'lang' in ctx:
                lang = ctx['lang']
            langMapObjs = self.env['connector.language.mapping'].search(
                [('instance_id', '=', instance_id])
            ctx['translation_sync'] ={}
            for langMapObj in langMapObjs:
                ctx['lang']=langMapObj.name
                ctx['translation_sync'].update({langMapObj.ecommerce_lang_id:{'name':categ_obj.with_context(ctx).name}})
        return ctx

    def _update_specific_category(self, updt_map_objs, channel, instance_id, connection):
        updted_category_ids, not_updted_category_ids, updted_category_mapping_ids, = [], [], []
        for categ_map_obj in updt_map_objs:
            categ_obj = categ_map_obj.name
            ecomm_id = categ_map_obj.ecomm_id    ##object model of category
            odoo_id = categ_map_obj.id
            if categ_obj and ecomm_id:
                ecomm_cat_parent_id = self.get_ecomm_parent_id(categ_obj, instance_id, channel, connection)
                resp_translation = self.translationlang_sync(categ_obj,instance_id)
                if hasattr(self, 'update_%s_category' % channel):
                    response = getattr(self, 'update_%s_category' % channel)({'name': categ_obj.name, 'parent_id': ecomm_cat_parent_id}, ecomm_id, connection)
                    if response.get('status', False):
                        updted_category_ids.append(categ_obj.id)
                        updted_category_mapping_ids.append(categ_map_obj.id)
                        self.update_ecomm_connector_mapping('connector.category.mapping', channel, {'ecomm_id':ecomm_id, 'name':categ_obj.name, 'created_by': 'odoo'}, connection)
                    else:
                        not_updted_category_ids.append(categ_obj.id)
            else:
                not_updted_category_ids.append(categ_obj.id)
        return updted_category_ids, not_updted_category_ids, updted_category_mapping_ids
 

