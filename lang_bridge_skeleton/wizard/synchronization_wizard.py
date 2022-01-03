# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
#
##############################################################################

from odoo import api, fields, models


class SynchronizationWizard(models.TransientModel):
    _inherit = 'synchronization.wizard'

    translation_sync = fields.Boolean(
        'Translation Synchronization',
        help="Enable to sync translated data for all mapped languages",default=True)

   
    def start_category_synchronization(self):
        ctx = dict(self._context or {})
        ctx['translation_sync'] = self.translation_sync
        return super(SynchronizationWizard, self.with_context(ctx)
                     ).start_category_synchronization()


    def start_category_synchronization_mapping(self):
        ctx = dict(self._context or {})
        ctx['translation_sync'] = self.translation_sync
        return super(SynchronizationWizard, self.with_context(ctx)
                     ).start_category_synchronization_mapping()

   
    def start_product_synchronization(self):
        ctx = dict(self._context or {})
        ctx['translation_sync'] = self.translation_sync
        return super(SynchronizationWizard, self.with_context(ctx)
                     ).start_product_synchronization()

   
    def start_product_synchronization_mapping(self):
        ctx = dict(self._context or {})
        ctx['translation_sync'] = self.translation_sync
        return super(SynchronizationWizard, self.with_context(ctx)
                     ).start_product_synchronization_mapping()
