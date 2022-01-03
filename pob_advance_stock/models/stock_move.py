 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

from odoo import fields,models,api
from odoo import tools
import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
	_inherit="stock.move"
	
	def prestashop_stock_update(self, erp_product_id, warehouse_id):
		check_mapping = self.env['connector.product.mapping'].sudo().search([('name','=',erp_product_id)],limit=1)
		if check_mapping:
			ctx = dict(self._context or {})
			map_obj = check_mapping[0]
			presta_product_id = map_obj.ecomm_id
			presta_product_attribute_id = map_obj.ecomm_combination_id
			instance_id = map_obj.instance_id ##instance obj from connector.product.mapping
			if instance_id:
				ctx.update({'instance_id':instance_id.id})
				connection = self.env['connector.instance'].sudo().with_context(ctx)._create_prestashop_connection()
				if connection['status'] and instance_id.inventory_sync == 'enable':
					if instance_id.advance_stock:
						if (instance_id.connector_stock_action == 'qoh'  and ctx['stock_operation'] == '_action_done')\
				 				or (instance_id.connector_stock_action != 'qoh' and \
					  		(ctx['stock_operation'] == '_action_cancel' or ctx['stock_operation'] == '_action_confirm')):
							check_in = False
							check_out = False
							mapping_id =  self.env['wk.advance.stock'].search([('location','=',
							self.location_dest_id.id)],limit=1)
							if mapping_id and ctx['stock_operation'] in ['_action_confirm','_action_done']:
								check_in = True
							else:
								if mapping_id and ctx['stock_operation'] == '_action_cancel':
									check_out = True
								else:
									mapping_id =  self.env['wk.advance.stock'].search([('location','=',
								self.location_id.id)],limit=1)
									if mapping_id:
										check_out = True
							if mapping_id:
								currency_id = mapping_id.currency_id
								ecomm_warehouse_id = mapping_id.presta_warehouse_id
								if check_in or check_out:
									prestashop = connection.get('prestashop',False)
									product_qty = int(self.product_qty)
									response = self.update_ecomm_quantity(prestashop,erp_product_id,warehouse_id,
																	presta_product_id,presta_product_attribute_id,
																	product_qty,currency_id,ecomm_warehouse_id,
																	instance_id,check_in,check_out)
									stock_obj = self.env['pob.advance.stock.history']
									state = 'draft'
									operation = 'check_in'
									odoo_location_id = self.location_dest_id.id
									if response[0]==1:
										state = 'done'
									if check_out:
										operation = 'check_out'
										odoo_location_id = self.location_id.id
									stock_obj.sudo().create(
										{
											'quantity'  : product_qty,
											'product_id': erp_product_id,
											'message' : response[1],
											'odoo_location_id': odoo_location_id,
											'state':state,
											'instance_id': instance_id.id,
											'operation' : operation
										})
					else:
						return super(StockMove,self).prestashop_stock_update(erp_product_id, warehouse_id)
		return True

	def update_ecomm_quantity(self,prestashop,erp_product_id,warehouse_id,
							presta_product_id,presta_product_attribute_id,
							product_qty,currency_id,ecomm_warehouse_id,
							instance_id,check_in=False,check_out=False):
		message = 'Message:'
		product_price =  self.env['product.product'].browse(erp_product_id)
		id_employee = instance_id.employee_id
		stock_op = 'add'
		id_stock_mvt_reason = 1
		if check_out:    ##outgoing
			stock_op = 'remove'
			id_stock_mvt_reason = 2
		try:
			stock = prestashop.get('erp_advance_stock_merges',options={'schema':'blank'})
			stock['erp_advance_stock_merges'].update({
					'id_product': presta_product_id, 
					'id_product_attribute': presta_product_attribute_id, 
					'quantity': abs(product_qty),
					'id_currency':currency_id,
					'id_warehouse': ecomm_warehouse_id, 
					'id_stock_mvt_reason': id_stock_mvt_reason,
					'id_employee': id_employee, 
					'price': str(product_price.lst_price), 
					'type': stock_op,
					'created_by': 'Odoo', 
				})
		except Exception as e:
			message += str(e)
			return [0,message]
		try:
			stock_data = prestashop.add('erp_advance_stock_merges',stock)
		except Exception as e:
			message+= str(e)
			return [0,message]
		if stock_data:
			status = True
			message += 'Successfull Updated'
			return [1,message]
		return [0,False]
