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

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def create_prestashop_product_attribute(self , name, odoo_id, connection, ecomm_attribute_code):
        prestashop = connection.get('prestashop', False)
        status = False
        ecomm_id = False
        add_data = False
        error = ''
        if prestashop:
            try:
                add_data = prestashop.get('product_options', options={'schema': 'blank'})
            except Exception as e:
                error = str(e)
            if add_data:
                add_data['product_option'].update({
                                            'group_type': 'select',
                                            'position':'0'
                                        })
                if type(add_data['product_option']['name']['language']) == list:
                    for i in range(len(add_data['product_option']['name']['language'])):
                        add_data['product_option']['name']['language'][i]['value'] = name
                        add_data['product_option']['public_name']['language'][i]['value'] = name
                else:
                    add_data['product_option']['name']['language']['value'] = name
                    add_data['product_option']['public_name']['language']['value'] = name
                try:
                    ecomm_id = prestashop.add('product_options', add_data)
                except:
                    error = str(e)
                if ecomm_id:
                    status = True
        return {
            'status' : status,
            'ecomm_id':ecomm_id,
            'error' : error
            }

    def  create_prestashop_product_attribute_value(self, ecomm_id, attribute_obj, ecomm_attribute_code, instance_id, connection):
        prestashop = connection.get('prestashop', False)
        status = True
        add_value = False
        error = ''
        if prestashop:
            try:
                add_value = prestashop.get('product_option_values', options={'schema': 'blank'})
            except Exception as e:
                status = False
                error = str(e)
            if add_value:
                for attribute_value_id in attribute_obj.value_ids:
                    if not self.env['connector.option.mapping'].search([('odoo_id', '=', attribute_value_id.id), ('instance_id','=',instance_id)]):
                        add_value['product_option_value'].update({
                                                    'id_attribute_group': ecomm_id,
                                                    'position':'0'
                                                })
                        if type(add_value['product_option_value']['name']['language']) == list:
                            for i in range(len(add_value['product_option_value']['name']['language'])):
                                add_value['product_option_value']['name']['language'][i]['value'] = attribute_value_id.name
                        else:
                            add_value['product_option_value']['name']['language']['value'] = attribute_value_id.name
                        try:
                            ecomm_attr_id = prestashop.add('product_option_values', add_value)
                        except Exception as e:
                            status = False
                            error = str(e)
                        if status:
                            self.create_odoo_connector_mapping('connector.option.mapping', ecomm_attr_id, 
                                                                attribute_value_id.id, instance_id,
                                                                ecomm_attr_id = ecomm_id ,
                                                                odoo_attr_id = attribute_obj.id)

                            self.create_ecomm_connector_mapping('connector.option.mapping', 'prestashop', 
                                                                {'ecomm_id':ecomm_attr_id,
                                                                'ecomm_attr_id':ecomm_id,
                                                                'odoo_id':attribute_value_id.id,
                                                                'odoo_attr_id':attribute_obj.id,
                                                                'name':attribute_value_id.name,
                                                                'created_by': 'odoo'}, connection)
        return {
            'status': True,
            'error':error
        }
                                                    