# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api, fields, models, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    # _name = "pob.config.settings"
    _inherit = 'res.config.settings'

    @api.model
    def _install_modules(self, modules):
        """Install the requested modules.
            return the next action to execute

          modules is a list of tuples
            (mod_name, browse_record | None)
        """
        response  = super(ResConfigSettings, self)._install_modules(modules)
        if response:
            if 'tag' in response == True:
                pob_modules = ''
                if response['tag'] == 'apps':
                    for module in response['params']['modules']:
                        if module.startswith('pob_extension'):
                            pob_modules = pob_modules+ "<h3>&#149; ' %s ' </h3><br />"%(module)
                    if pob_modules:
                        message="<h2>Following POB Extensions are not found on your odoo -</h2><br /><br />"
                        message=message+pob_modules
                        message=message+'<br /><br />Raise a Ticket at <a href="http://webkul.com/ticket/open.php" target="_blank">Click me</a>'
                        partial_id = self.env['pob.message'].create({'text':message})
                        return {
                                'name':_("Message"),
                                'view_mode': 'form',
                                'view_id': False,
                                'view_type': 'form',
                                'res_model': 'pob.message',
                                'res_id': partial_id.id,
                                'type': 'ir.actions.act_window',
                                'nodestroy': True,
                                'target': 'new',
                                'domain': '[]',
                                'context': self._context
                                }
            else : return None
        return response




    @api.model
    def _get_default_category(self):
        cat_ids = self.env['product.category'].search([])
        if not cat_ids:
            raise UserError(_('There is no category found on your Odoo ! Please create one.'))
        return cat_ids[0]

    @api.model
    def _get_default_location(self):
        location_ids = self.env['stock.location'].search([('usage', '=','internal')])
        if not location_ids:
            return False
        return location_ids[0]

    #@api.multi
    def _get_default_team(self):
        team_id = self.env['crm.team'].search([('name','=','Prestashop')])
        return team_id

    pob_default_stock_location = fields.Many2one('stock.location', 'Stock Location',domain=[('usage', '=','internal')], required=True, default=_get_default_location)
    pob_default_category = fields.Many2one('product.category', 'Default Category', required=True, default=_get_default_category)
    team_id = fields.Many2one('crm.team', 'Sales Team', default=_get_default_team)
    salesperson = fields.Many2one('res.users', 'Salesperson', default=lambda self: self.env.user)
    payment_term = fields.Many2one('account.payment.term', 'Payment Term')
    delivered = fields.Boolean("Delivery status")
    invoiced = fields.Boolean("Invoicing status")
    cancelled = fields.Boolean("Cancelled orders")

    module_pob_extension_stock = fields.Boolean("Real-Time Stock Synchronization")
    module_pob_extension_multilang = fields.Boolean("Multi-Language Synchronization")

    pob_delivery_product = fields.Many2one('product.product',"Delivery Product",
        help="""Service type product used for Delivery purposes.""")
    pob_discount_product = fields.Many2one('product.product',"Discount Product",
        help="""Service type product used for Discount purposes.""")
    stock_type = fields.Selection(selection=[('forecast','Forecast Quantity'),('onhand','On-Hand Quantity')],string="Stock Type",default='onhand')


    #@api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_values = self.env['ir.default']
        # config = self.browse(self.ids[0])
        if self.pob_delivery_product:
            ir_values.sudo().set('res.config.settings', 'pob_delivery_product', str(self.pob_delivery_product.id) )
        if self.pob_discount_product.id:
            ir_values.sudo().set('res.config.settings', 'pob_discount_product', str(self.pob_discount_product.id) )
        _logger.info("===============nbhkhjk========>%r",self.pob_discount_product)
        _logger.info("===============nbhkhjk========>%r",self.pob_delivery_product)
        pob_values = self.env['prestashop.configure'].search([('active','=',True)])
        if pob_values:
            pob_values.pob_default_stock_location   = self.pob_default_stock_location
            pob_values.pob_default_category         = self.pob_default_category
            pob_values.team_id                      = self.team_id
            pob_values.salesperson                  = self.salesperson
            pob_values.payment_term                 = self.payment_term
            pob_values.delivered                    = self.delivered
            pob_values.invoiced                     = self.invoiced
            pob_values.cancelled                    = self.cancelled
            pob_values.stock_type                   = self.stock_type
        return True

    #@api.multi
    def pob_reset_mapping(self):
        orders = self.env['wk.order.mapping'].search([])
        if orders:
            orders.unlink()
        customer = self.env['prestashop.customer'].search([])
        if customer:
            customer.unlink()
        template = self.env['prestashop.product.template'].search([])
        if template:
            template.unlink()
        product = self.env['prestashop.product'].search([])
        if product:
            product.unlink()
        attribute = self.env['prestashop.product.attribute'].search([])
        if attribute:
            attribute.unlink()
        value = self.env['prestashop.product.attribute.value'].search([])
        if value:
            value.unlink()
        category = self.env['prestashop.category'].search([])
        if category:
            category.unlink()
        wizard = self.env['pob.message'].create({'text':"All POB Mappings removed successfully!!"})
        return {
                    'name':_("Test Result"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'pob.message',
                    'res_id': wizard.id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': self._context
                }

    #@api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        values = res
        ir_values = self.env['ir.default']
        # config = self.browse(self.ids[0])
        pob_delivery_product = ir_values.sudo().get('res.config.settings', 'pob_delivery_product')
        _logger.info("===============get_values========>%r",pob_delivery_product)
        
        pob_discount_product = ir_values.sudo().get('res.config.settings', 'pob_discount_product')
        _logger.info("==========================================+++++>%r",[pob_delivery_product,pob_discount_product])
        pob_values = self.env['prestashop.configure'].sudo().search([('active','=',True)],limit=1)
        try:
            pob_discount_product = int(pob_discount_product)
        except:
            pob_discount_product = False
        try:
            pob_delivery_product = int(pob_delivery_product)
        except:
            pob_delivery_product = False
        values.update({
        'pob_default_stock_location'                : pob_values.pob_default_stock_location.id or False,
        'pob_default_category'                      : pob_values.pob_default_category.id or False,
        'team_id'                                   : pob_values.team_id.id or False,
        'salesperson'                               : pob_values.salesperson.id or False,
        'payment_term'                              : pob_values.payment_term.id or False,
        'delivered'                                 : pob_values.delivered or False,
        'invoiced'                                  : pob_values.invoiced or False,
        'cancelled'                                 : pob_values.cancelled or False,
        'pob_discount_product'                      : pob_discount_product,
        'pob_delivery_product'                      : pob_delivery_product,
        'stock_type'                                : pob_values.stock_type
        })

        return values
        
class CrmTeam(models.Model):
    
    _inherit = ['crm.team']

    @api.model
    def create_sales_team(self):
        search = self.search([('name','=','Prestashop')])
        if not search:
            self.create({'name':'Prestashop','use_quoatation':True,'code':'PS','use_invoices':True})
    