# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import api,models,fields 

class PobSynchronizationHistory(models.Model):
    _name = "pob.synchronization.history"

    name   = fields.Char(string="Name")
    status = fields.Selection([
        ('yes', 'Successfull'),
        ('no', 'Un-Successfull')
    ], string='Status')
    action_on = fields.Selection([
        ('product', 'Product'),
        ('category', 'Category'),
        ('customer', 'Customer'),
        ('order', 'Order')
    ], string='Action On')
    action = fields.Selection([
        ('a', 'Import'),
        ('b', 'Export'),
        ('c', 'Update')
    ], string='Action')
    create_date = fields.Datetime(string='Created Date')
    error_message = fields.Text(string='Summary')