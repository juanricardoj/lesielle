from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class ConnectorSnippet(models.TransientModel):
	_inherit = 'connector.snippet'

	@api.model
	def prestashop_after_order_invoice(self , connection, ecommerce_reference , id_order):
		prestashop = connection.get('prestashop', False)
		id_employee = connection.get('id_employee',False)
		return self.update_order_status_prestashop(prestashop, id_order, 2,id_employee)
	
	@api.model
	def prestashop_after_order_cancel(self , connection, ecommerce_reference , id_order):
		prestashop = connection.get('prestashop', False)
		id_employee = connection.get('id_employee',False)
		return self.update_order_status_prestashop(prestashop, id_order, 6, id_employee)

	@api.model
	def prestashop_after_order_shipment(self , connection, ecommerce_reference , id_order):
		prestashop = connection.get('prestashop', False)
		id_employee = connection.get('id_employee',False)
		return self.update_order_status_prestashop(prestashop, id_order, 4,id_employee)

	def update_order_status_prestashop(self, prestashop, id_order, id_order_state,id_employee=False):
		status = 'no'
		text = 'Status Successfully Updated'
		try:
			order_his_data = prestashop.get('order_histories', options={'schema': 'blank'})
			order_his_data['order_history'].update({
			'id_order' : id_order,
			'id_order_state' : id_order_state
			})
			call_api = 'order_histories?sendemail=1'
			if id_employee:
				call_api+= '&id_employee=%s'%id_employee
			state_update = prestashop.add(call_api, order_his_data)
			status = 'yes'
		except Exception as e:
			text = 'Status Not Updated For Order Id '+ str(id_order) + ' And Error is ' + str(e)
		return{
			'status':status,
			'text' : text
		}

