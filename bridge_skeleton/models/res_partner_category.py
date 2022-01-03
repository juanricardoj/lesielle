# -*- coding: utf-8 -*-
##########################################################################
#
#
##########################################################################

from odoo import api, fields, models


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    id_group = fields.Integer()
    id_lang = fields.Integer()