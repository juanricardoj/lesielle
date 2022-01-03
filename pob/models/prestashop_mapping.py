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
from odoo.exceptions import Warning
from . import prestapi
from .prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError

mapping_dict = {
    'connector.option.mapping':'erp_attribute_values_merges',
    'connector.attribute.mapping' : 'erp_attributes_merges',
    'connector.category.mapping' : 'erp_category_merges',
    'connector.template.mapping' : 'erp_product_template_merges',
    'connector.product.mapping' : 'erp_product_merges'
}
class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def create_prestashop_connector_mapping(self, model, data, connection):
        prestashop = connection.get('prestashop' , False)
        if prestashop:
            try:
                resource_data  = prestashop.get(mapping_dict[model], options={'schema': 'blank'})
            except Exception as e:
                raise Warning(' Error in Creating blank schema for resource.')
            if resource_data:
                if model == 'connector.option.mapping':
                    resource_data['erp_attribute_values_merge'].update({
                        'erp_attribute_id':data['odoo_attr_id'],
                        'erp_attribute_value_id':data['odoo_id'],
                        'prestashop_attribute_value_id':data['ecomm_id'],
                        'prestashop_attribute_id':data['ecomm_attr_id'],
                        'created_by':'Odoo',
                        })
                elif model == 'connector.attribute.mapping':
                    resource_data['erp_attributes_merge'].update({
                        'erp_attribute_id':data['odoo_id'],
                        'prestashop_attribute_id':data['ecomm_id'],
                        'created_by':'Odoo',
                        })
                elif model == 'connector.category.mapping':
                    resource_data['erp_category_merge'].update({
                    'erp_category_id':data['odoo_id'],
                    'prestashop_category_id':data['ecomm_id'],
                    'created_by':'Odoo',
                    })
                elif model == 'connector.template.mapping':
                    resource_data['erp_product_template_merge'].update({
                    'erp_template_id':data['odoo_id'],
                    'presta_product_id':data['ecomm_id'],
                    'created_by':'Odoo',
                    })
                elif model == 'connector.product.mapping':
                    resource_data['erp_product_merge'].update({
                    'erp_product_id':data['odoo_id'],
                    'erp_template_id':data['prod_tmpl_id'],
                    'prestashop_product_id':data['presta_product_id'],
                    'prestashop_product_attribute_id':data.get('ecomm_id','0'),
                    'created_by':'Odoo',
                    })
                try:
                    return_id = prestashop.add( mapping_dict[model], resource_data)
                except Exception as e:
                    raise Warning(' Error in Creating Entry in Prestashop For '+ mapping_dict[model] + 'error is' + str(e))