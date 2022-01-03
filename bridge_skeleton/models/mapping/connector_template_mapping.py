# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, api, models
import logging
_logger = logging.getLogger(__name__)

class ConnectorTemplateMapping(models.Model):
    _name = "connector.template.mapping"
    _inherit = ['connector.common.mapping']
    _order = 'id desc'
    _description = "Ecomm Product Template"

    name = fields.Many2one('product.template', string='Template Name')
    is_variants = fields.Boolean(string='Is Variants')

    @api.model
    def create_template_mapping(self, data):
        if data.get('odoo_id'):
            ctx = dict(self._context or {})
            template_obj = self.env['product.product'].browse(
                data.get('odoo_id')).product_tmpl_id
            if not template_obj.attribute_line_ids :
                odooMapDict = {
                    'name' : template_obj.id,
                    'odoo_id' : template_obj.id,
                    'ecomm_id' : data.get('ecomm_id'),
                    'instance_id' : ctx.get('instance_id'),
                    'created_by' : 'Manual Mapping'
                }
                res = self.create(odooMapDict)
        return True

    @api.model
    def create_n_update_attribute_line(self, data):
        line_dict = {}
        _logger.info("==========create_n_update_attribute_line============ : %r", data['values'])
        if data.get('product_tmpl_id'):
            template_id = data.get('product_tmpl_id', 0)
            attribute_id = data.get('attribute_id', 0)
            domain = [('product_tmpl_id', '=', template_id)]
            if 'values' in data:
                value_ids = []
                prod_attr_price_model = self.env['product.template.attribute.value']
                for value in data.get('values', {}):
                    value_id = value.get('value_id', 0)
                    value_ids.append(value_id)
                    # if value.get('price_extra'):
                    #     price_extra = value['price_extra']
                    #     search_domain = domain + [('product_attribute_value_id', '=', value_id)]
                    #     attr_price_objs = prod_attr_price_model.search(search_domain)
                    #     if attr_price_objs:
                    #         for attr_price_obj in attr_price_objs:
                    #             attr_price_obj.write({'price_extra': price_extra})
                    #     else:
                    #         attr_price_dict = {
                    #             'product_tmpl_id' : template_id,
                    #             'product_attribute_value_id' : value_id,
                    #             'price_extra' : price_extra,
                    #         }
                    #         prod_attr_price_model.create(attr_price_dict)
                line_dict['value_ids'] = [(6, 0, value_ids)]
            search_domain = domain + [('attribute_id', '=', attribute_id)]
            prod_attr_line_model = self.env['product.template.attribute.line']
            exist_attr_line_objs = prod_attr_line_model.search(search_domain)
            _logger.info("==========exist_attr_line_objs============ : %r", exist_attr_line_objs)
            if exist_attr_line_objs:
                for exist_attr_line_obj in exist_attr_line_objs:
                    exist_attr_line_obj.with_context({'update_product_template_attribute_values':False}).write(line_dict)
            else:
                line_dict.update({
                    'attribute_id' : attribute_id,
                    'product_tmpl_id' : template_id
                })
                a = prod_attr_line_model.create(line_dict)
                _logger.info("==========prod_attr_line_model============ : %r", a)
            return True
        return False
