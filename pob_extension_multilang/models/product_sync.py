# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def export_template(self, prestashop , template_data , instance_id , channel, connection):
        status = True
        error = ''
        prestashop_product_id = 0
        product_schema = False
        try:
            product_schema = prestashop.get('products', options = {'schema':'blank'})
        except Exception as e:
            status = False
            error = str(e)
        if product_schema:
            ps_categ_id = self.sync_categories(template_data.categ_id, instance_id, channel, connection)
            ps_extra_categ = []
            for j in template_data.connector_categ_ids.categ_ids:
                ps_ex_cat_id = self.sync_categories(j , instance_id, channel, connection )
                ps_extra_categ.append({'id':str(ps_ex_cat_id)})
            product_schema['product'].update({
                            'price': str(round(template_data.list_price,6)),
                            'active':'1',
                            'redirect_type':'404',
                            'minimal_quantity':'1',
                            'available_for_order':'1',
                            'show_price':'1',
                            'state':'1',
                            'reference': str(template_data.default_code or ''),
                            'out_of_stock':'2',
                            'condition':'new',
                            'id_category_default':str(ps_categ_id),
                            'weight' : str(template_data.weight or ''),
                            'ean13': str(template_data.barcode or '')
                        })
            if template_data.standard_price:
                product_schema['product']['wholesale_price'] = str(round(template_data.standard_price,6))
            if self._context.get('translation_sync'):
                ctx_data = self._context.get('translated_values',{})
            else:
                ctx_data = {}
            if type(product_schema['product']['name']['language']) == list:
                for i in range(len(product_schema['product']['name']['language'])):
                    lang_id = product_schema['product']['name']['language'][i]['attrs']['id']
                    if lang_id in ctx_data:
                        product_schema['product']['name']['language'][i]['value'] = ctx_data[lang_id]['name']
                        product_schema['product']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite('', ctx_data[lang_id]['name'])
                        product_schema['product']['description']['language'][i]['value'] = ctx_data[lang_id]['description']
                        product_schema['product']['description_short']['language'][i]['value'] = ctx_data[lang_id]['description_sale']
                    else:
                        product_schema['product']['name']['language'][i]['value'] = template_data.name
                        product_schema['product']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite('', template_data.name)
                        product_schema['product']['description']['language'][i]['value'] = template_data.description
                        product_schema['product']['description_short']['language'][i]['value'] = template_data.description_sale
            else:
                product_schema['product']['name']['language']['value'] = template_data.name
                product_schema['product']['link_rewrite']['language']['value'] = self._get_link_rewrite('', template_data.name)
                product_schema['product']['description']['language']['value'] = template_data.description
                product_schema['product']['description_short']['language']['value'] = template_data.description_sale
            if type(product_schema['product']['associations']['categories']['category'])== list:
                product_schema['product']['associations']['categories']['category'] = product_schema['product']['associations']['categories']['category'][0]
            product_schema['product']['associations']['categories']['category']['id'] = str(ps_categ_id)
            pop_attr = product_schema['product']['associations'].pop('combinations',None)
            a1 = product_schema['product']['associations'].pop('images',None)
            a2 = product_schema['product'].pop('position_in_category',None)
            if ps_extra_categ:
                a3 = product_schema['product']['associations']['categories']['category'] = ps_extra_categ
            try:
                prestashop_product_id = prestashop.add('products', product_schema)
            except Exception as e:
                status = False
                error = str(e)
        return{
            'status': status,
            'error' : error,
            'prestashop_product_id':prestashop_product_id
            }
 

    def update_template(self, prestashop, product_data, tmpl_id, ecomm_id, ps_lang_id):
        status = False
        error = ''
        product_data['product']['price'] = str(round(tmpl_id.list_price,6))
        product_data['product']['wholesale_price'] = str(round(tmpl_id.standard_price,6))
        product_data['product']['weight'] = str(tmpl_id.weight or '')
        product_data['product']['reference'] = str(tmpl_id.default_code or '')
        product_data['product']['ean13'] = str(tmpl_id.barcode or '')
        if self._context.get('translation_sync'):
            ctx_data = self._context.get('translated_values',{})           
        else:
            ctx_data = {}
        if type(product_data['product']['name']['language']) == list:
            for i in range(len(product_data['product']['name']['language'])):
                lang_id = product_data['product']['name']['language'][i]['attrs']['id']
                if lang_id in ctx_data:
                    product_data['product']['name']['language'][i]['value'] =  ctx_data[lang_id]['name'] or ''
                    product_data['product']['description']['language'][i]['value'] = ctx_data[lang_id]['description'] or ''
                    product_data['product']['description_short']['language'][i]['value'] = ctx_data[lang_id]['description_sale'] or ''
                elif lang_id== str(ps_lang_id):
                    product_data['product']['name']['language'][i]['value'] = 	tmpl_id.name or ''
                    product_data['product']['description']['language'][i]['value'] = tmpl_id.description or ''
                    product_data['product']['description_short']['language'][i]['value'] = tmpl_id.description_sale or ''
        else:
            product_data['product']['name']['language']['value'] = tmpl_id.name or ''
            product_data['product']['description']['language']['value'] = tmpl_id.description or ''
            product_data['product']['description_short']['language']['value'] = tmpl_id.description_sale or ''
        a1 = product_data['product'].pop('position_in_category',None)
        a2 = product_data['product'].pop('manufacturer_name',None)
        a3 = product_data['product'].pop('quantity',None)
        a4 = product_data['product'].pop('type',None)
        try:
            returnid = prestashop.edit('products', ecomm_id, product_data)
        except Exception as e:
            error = str(e)
        if returnid:
            status = True
            if 'image' not in product_data['product']['associations']['images']:
                if tmpl_id.image_1920:
                    get = self.create_images(prestashop, tmpl_id.image_1920, ecomm_id)
        return{
            'status':status,
            'error' : error
        }
          