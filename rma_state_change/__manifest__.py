# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
{
    "name": "POB: rma state change",
    "category": 'hidden',
    "summary": """
        This module will allow you to change prestawshop state according to rma create in odoo.""",
    "description": """
====================
**Help and Support**
====================

|icon_help| `Help <http://webkul.uvdesk.com/en/customer/create-ticket/>`_ |icon_support| `Support <http://webkul.uvdesk.com/en/customer/create-ticket/>`_ |icon_features| `Request new Feature(s) <http://webkul.uvdesk.com/en/customer/create-ticket/>`_
    """,
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "website": "http://www.webkul.com",
    "version": '1.0',
    "depends": ['pob','rma'],
	"data":['views/connector_order_mapping.xml',
	'views/connector_instance.xml'],
    "installable": True,
    "application": True,
    "auto_install": False
}
