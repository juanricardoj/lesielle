from odoo import api, fields, models, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ConnectorInstance(models.Model):
    _inherit = 'connector.instance'
    

    @api.model
    def _get_default_locationn(self):
        res = self.env['stock.warehouse'].search([])
        if res:
            return res[0]
        else:
            return False
    
    pob_warehouse_used = fields.Selection([('all', 'ALL'),
                                                ('specific', 'SPECIFIC'),
                                                ], 'Odoo`s Warehouse(s) used with POB',required=True, default = 'all')
    pob_default_warehouse = fields.Many2one('stock.warehouse', 'Default Warehouse',required=True, default=_get_default_locationn)


    def get_default_warehouse_ids(self, instance_id):
        warehouse_ids = []
        if instance_id:
            instance_id = self.browse(instance_id)
            if instance_id.pob_warehouse_used == 'specific':
                warehouse_ids.append(instance_id.pob_default_warehouse.id)
            else:
                search = self.env['stock.warehouse'].search([])
                warehouse_ids.extend(search.ids)
        return warehouse_ids

    
    