# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

# Attribute Sync Operation

from odoo import api, models
import logging
_logger = logging.getLogger(__name__)

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"
    
    def create_prestashop_category(self ,odoo_id, parent_categ_id , name ,connection):
        prestashop = connection.get('prestashop', False)
        status = False
        ecomm_id = False
        cat_data = False
        error = ''
        if parent_categ_id == 1:
            parent_categ_id = 2
        if prestashop:
            try:
                cat_data = prestashop.get('categories', options={'schema': 'blank'})
            except Exception as e:
                error = str(e)
            if cat_data:
                if type(cat_data['category']['name']['language']) == list:
                    for i in range(len(cat_data['category']['name']['language'])):
                        cat_data['category']['name']['language'][i]['value'] = name
                        cat_data['category']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite(zip, name)
                        cat_data['category']['description']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_description']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_keywords']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_title']['language'][i]['value'] = name
                else:
                    cat_data['category']['name']['language']['value'] = name
                    cat_data['category']['link_rewrite']['language']['value'] = self._get_link_rewrite(zip, name)
                    cat_data['category']['description']['language']['value'] = 'None'
                    cat_data['category']['meta_description']['language']['value'] = 'None'
                    cat_data['category']['meta_keywords']['language']['value'] = 'None'
                    cat_data['category']['meta_title']['language']['value'] = name
                cat_data['category']['is_root_category'] = '0'
                cat_data['category']['id_parent'] = parent_categ_id
                cat_data['category']['active'] = '1'
                try:
                    ecomm_id = prestashop.add('categories', cat_data)
                except:
                    error = str(e)
                if ecomm_id:
                    status = True
        return {
            'status' : status,
            'ecomm_id' : ecomm_id,
            'error' : error
            }
    
    def update_prestashop_category(self, vals , ecomm_id , connection):
        prestashop = connection.get('prestashop', False)
        status = False
        name = vals.get('name', '')
        cat_data = False
        error = ''
        if vals.get('parent_id') == 1:
            parent_categ_id = 2
        else:
            parent_categ_id = vals.get('parent_id', False)
        if prestashop and name:
            try:
                cat_data = prestashop.get('categories', ecomm_id)
            except Exception as e:
                error = str(e)
            if cat_data:
                if type(cat_data['category']['name']['language']) == list:
                    for i in range(len(cat_data['category']['name']['language'])):
                        cat_data['category']['name']['language'][i]['value'] = name
                        cat_data['category']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite(zip, name)
                        cat_data['category']['description']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_description']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_keywords']['language'][i]['value'] = 'None'
                        cat_data['category']['meta_title']['language'][i]['value'] = name
                else:
                    cat_data['category']['name']['language']['value'] = name
                    cat_data['category']['link_rewrite']['language']['value'] = self._get_link_rewrite(zip, name)
                    cat_data['category']['description']['language']['value'] = 'None'
                    cat_data['category']['meta_description']['language']['value'] = 'None'
                    cat_data['category']['meta_keywords']['language']['value'] = 'None'
                    cat_data['category']['meta_title']['language']['value'] = name
                cat_data['category']['id_parent'] = parent_categ_id or '2'
                a1 = cat_data['category'].pop('level_depth',None)
                a2 = cat_data['category'].pop('nb_products_recursive',None)
                try:
                    ecomm_data = prestashop.edit('categories', ecomm_id, cat_data)
                except:
                    error = str(e)
                if ecomm_data:
                    status = True
        return {
            'status' : status,
            'error' : str(e)
            }

