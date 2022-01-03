# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields,api,models
from odoo.addons.pob.models import prestapi
from odoo.exceptions import UserError,Warning
from odoo.tools.translate import _
from odoo.addons.pob.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError
import logging

_logger = logging.getLogger(__name__)


class PobAdvanceStockHistory(models.Model):
    _name = 'pob.advance.stock.history'


    quantity  = fields.Integer('Quantity')
    message = fields.Text('Message')
    odoo_location_id   = fields.Integer('Odoo Location Id')
    product_id = fields.Integer('Product Id')
    state = fields.Selection([('done','Done'),('draft','Draft')], string = 'Advance Stock State')
    instance_id = fields.Many2one('connector.instance', 'Instance Id')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)
    operation = fields.Selection([('check_in','Add Stock'),('check_out','Remove Stock')], string = 'Stock Operation')


    @api.model
    def action_failed_sychronise_stock(self):
        message = 'Message:'
        warehouse_mapping = self.env['wk.advance.stock']
        product_mapping = self.env['connector.product.mapping']
        connector_instance = self.env['connector.instance']
        success_ids = []
        unsucess_ids = []
        employee_id = False
        stock_data = False
        ctx = self._context.copy() or {}
        failed_ids = False 
        if 'active_ids' in ctx:
            mappingIds = ctx['active_ids']
            history_mapped = self.browse(mappingIds)
            instance_ids = history_mapped.mapped('instance_id')
            failed_ids = history_mapped.filtered(lambda his: his.state!='done')
            for instance_id in instance_ids:
                stock_data = False
                ctx.update({'instance_id':instance_id.id})
                connection = connector_instance.with_context(ctx)._create_prestashop_connection()
                if connection['status']:
                    prestashop = connection.get('prestashop', False)
                    if prestashop:
                        try:
                            stock = prestashop.get('erp_advance_stock_merges',options={'schema':'blank'})
                        except Exception as e:
                            raise Warning('Error %s')%str(e)
                        for history in failed_ids:
                            product_map_obj =  product_mapping.search([('odoo_id','=', history.product_id),
                            ('instance_id','=',instance_id.id)], limit =1)
                            if product_map_obj:
                                presta_product_id = product_map_obj.ecomm_id
                                presta_product_attribute_id = product_map_obj.ecomm_combination_id
                                advance_stock = warehouse_mapping.search([('location','=', history.odoo_location_id)])
                                if advance_stock:
                                    id_warehouse = advance_stock.presta_warehouse_id
                                    id_currency = advance_stock.currency_id
                                    if history.operation == 'check_out':
                                        id_stock_mvt_reason = 2
                                        stock_op = 'remove'
                                    else:
                                        id_stock_mvt_reason = 1
                                        stock_op = 'add'
                                    stock['erp_advance_stock_merges'].update(
                                        {
                                            'id_product_attribute': presta_product_attribute_id, 
                                            'id_product': presta_product_id, 
                                            'id_employee': instance_id.employee_id, 
                                            'type': stock_op,
                                            'price': str(product_map_obj.name.lst_price), 
                                            'id_warehouse': id_warehouse, 
                                            'id_stock_mvt_reason': id_stock_mvt_reason,
                                            'created_by': 'Openerp', 
                                            'id_currency':id_currency,
                                            'quantity': abs(history.quantity)
                                        })
                                    try:
                                        stock_data = prestashop.add('erp_advance_stock_merges', stock)
                                    except Exception as e:
                                        pass
                                    if stock_data:
                                        history.state = 'done'
                                        history.message = 'Message: Successfully Updated'            
                
                success_ids.extend(failed_ids.filtered(lambda his: his.state=='done').ids)
                unsucess_ids.extend(failed_ids.filtered(lambda his: his.state!='done').ids)
        if success_ids and not unsucess_ids:
            message = 'Message: Successfull Stocks Updated to Prestashop {}'.format(success_ids)
        if not success_ids and unsucess_ids:
            message = 'Message: Unsuccessfull Ids Exported To Prestashop {}'.format(unsucess_ids)
        if success_ids and unsucess_ids:
            message = 'Message: Successfull Ids Update to Prestashop {} \n Unsuccessfull Ids Exported To Prestashop {}'.format(success_ids,unsucess_ids)
        if not failed_ids:
            message = 'All Stocks are already Synchronised!'
        return self.env['message.wizard'].genrated_message(message)
