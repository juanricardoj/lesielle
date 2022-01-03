from odoo import api, models, fields

class ConnectorSnippet(models.TransientModel):
    _inherit = 'connector.snippet'
    
    
    
    @api.model
    def get_quantity(self,obj_pro, instance_id):
        """
            to get quantity of product or product template
            @params : product template obj or product obj,instance_id
            @return : quantity in hand or quantity forecasted
        """
        quantity = 0.0
        config_id = self.env['connector.instance'].browse(instance_id)
        ctx = self._context.copy() or {}
        qty = obj_pro.with_context(ctx)._product_available()
        if config_id.connector_stock_action =="qoh":
            quantity = qty[obj_pro.id]['qty_available']
        else:
            quantity = qty[obj_pro.id]['virtual_available']
        if type(quantity) == str:
            quantity = quantity.split('.')[0]
        if type(quantity) == float:
            quantity = quantity.as_integer_ratio()[0]
        return quantity