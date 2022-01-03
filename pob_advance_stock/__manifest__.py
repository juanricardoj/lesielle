#!/usr/bin/env python
# -*- coding: utf-8 -*-

{
    'name': 'POB Advance Stock Extension',
    'version': '1.0',
	'sequence': 1,
	'summary':'Advance Stock Extension for POB',
    'category': 'A Module of Fairhall Solutions',
    'description': """
    This Module helps in maintaining stock( Advance Stock Management) from odoo to prestashop with real time.

	NOTE : This module works very well with prestashop 1.6.XX and Odoo 13.0.
    """,
    'author': 'Fairhall Solutions',
    'depends': ['pob', 'prestashop_bridge_multishop'],
    'website': 'http://www.webkul.com',
    'data' : [
                'security/ir.model.access.csv',
                'views/pob_advance_stock_view.xml',
                'views/pob_history.xml'
                ],
    'installable': True,
    'auto_install': False,
}
