# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)



class RmaRma(models.Model):
	_inherit = 'rma.rma'

	def write(self,vals):
		res = super().write(vals)
		if res:
			self.change_pob_rma_status()
		return res

	
	def change_pob_rma_status(self):
		rma_obj = self.filtered(lambda obj: obj.state=='resolved')
		connector_order = self.env['connector.order.mapping']
		connector_snippet = self.env['connector.snippet']
		connector_instance = self.env['connector.instance']
		context = self._context.copy() or {}
		if rma_obj:
			order_ids = rma_obj.mapped('order_id')
			for order_id in order_ids:
				connector_order = connector_order.search([('odoo_order_id','=',order_id.id),('refunded','=',False)])
				if connector_order:
					ecomm_order_id = connector_order.ecommerce_order_id
					instance_id = connector_order.instance_id
					order_status = instance_id.refund
					if order_status>0:
						check = False
						context.update({'instance_id':instance_id.id})
						connection = connector_instance.with_context(context)._create_prestashop_connection()
						prestashop = connection.get('prestashop',False)
						if prestashop:
							actual_lines = order_id.order_line.filtered(lambda order_line: order_line.product_id.type!= 'service')
							for order_line in actual_lines:
								ordered_qty = order_line.product_uom_qty
								rma_objs = self.search([('order_id','=',order_id.id),
								('orderline_id','=',order_line.id),('state','=','resolved')])
								refunded_qty = sum(rma_objs.mapped('refund_qty'))
								if refunded_qty<ordered_qty:
									order_status = instance_id.partial_refund
									check = True
									break
							if check and connector_order.partial_refund:
								continue
							try:
								order_his_data = prestashop.get('order_histories', options={'schema': 'blank'})
								order_his_data['order_history'].update({
								'id_order' : ecomm_order_id,
								'id_order_state' : order_status
								})
								state_update = prestashop.add('order_histories', order_his_data)
								if check:
									connector_order.partial_refund = True
								else:
									connector_order.refunded = True
							except:
								pass
		return True