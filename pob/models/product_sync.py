# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

# Product Sync Operation
from odoo import api, models
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)
class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"
    
    def _export_prestashop_specific_template(self , temp_obj, instance_id, channel, connection):
        """
        @param code: Obj pro, instance id , channel , connection
        @param context: A standard dictionary
        @return: Dictionary
        """
        prestashop = connection.get('prestashop', False)
        error = ''
        status = False
        is_variants = False
        if prestashop:
            product_data = self.export_template(prestashop ,temp_obj , instance_id , channel, connection)
            if product_data['status']:
                if temp_obj.attribute_line_ids:
                    is_variants = True
                self.create_odoo_connector_mapping('connector.template.mapping', 
                                        product_data['prestashop_product_id'], 
                                        temp_obj.id, 
                                        instance_id,
                                        is_variants = is_variants,
                                        name = temp_obj.id
                                        )
                self.create_ecomm_connector_mapping('connector.template.mapping', 'prestashop', 
                                                    {'odoo_id':temp_obj.id,
                                                    'ecomm_id':product_data['prestashop_product_id'],
                                                    'created_by': 'odoo'}, connection)
                self._cr.commit()
                status = True
            else:
                error = product_data['error'] + ' and product name is ' + str(temp_obj.name)
            if status:
                status = False
                if temp_obj.attribute_line_ids:
                    for product_id in temp_obj.product_variant_ids:
                        combination_data = self.create_combination(prestashop , product_id, product_data['prestashop_product_id'] , instance_id)
                        if combination_data['status']:
                            self.create_odoo_connector_mapping('connector.product.mapping', 
                                        product_data['prestashop_product_id'], 
                                        product_id.id, 
                                        instance_id,
                                        odoo_tmpl_id = temp_obj.id,
                                        ecomm_combination_id = combination_data['prestashop_comb_id'],
                                        name = product_id.id
                                        )
                            self.create_ecomm_connector_mapping('connector.product.mapping', 'prestashop', 
                                                                {'odoo_id':product_id.id,
                                                                'ecomm_id':combination_data['prestashop_comb_id'],
                                                                'prod_tmpl_id':temp_obj.id,
                                                                'presta_product_id': product_data['prestashop_product_id'],
                                                                'created_by': 'odoo'}, connection)
                            status = True
                        else:
                            error = combination_data['error'] + ' and product name is ' + str(temp_obj.name) + 'product.product id is' + str(product_id.id)
                else:
                    odoo_product_id = temp_obj.product_variant_ids[0].id
                    if temp_obj.image_1920:
                        get = self.create_images(prestashop, temp_obj.image_1920, product_data['prestashop_product_id'])
                    qty = temp_obj.product_variant_ids[0]._product_available()
                    quantity = qty[odoo_product_id]['qty_available'] - qty[odoo_product_id]['outgoing_qty']
                    if type(quantity) == str:
                        quantity = quantity.split('.')[0]
                    if type(quantity) == float:
                        quantity = quantity.as_integer_ratio()[0]
                    if float(quantity) > 0.0 :
                        get = self.update_quantity_prestashop(prestashop, product_data['prestashop_product_id'], quantity)
                        if get[0]==0:
                            error = str(get[1])
                    self.create_odoo_connector_mapping('connector.product.mapping', 
                                    product_data['prestashop_product_id'], 
                                    odoo_product_id, 
                                    instance_id,
                                    odoo_tmpl_id = temp_obj.id,
                                    ecomm_combination_id = 0,
                                    name = odoo_product_id)
                    self.create_ecomm_connector_mapping('connector.product.mapping', 'prestashop', 
                                                                {'odoo_id':odoo_product_id,
                                                                'ecomm_id':0,
                                                                'prod_tmpl_id':temp_obj.id,
                                                                'presta_product_id': product_data['prestashop_product_id'],
                                                                'created_by': 'odoo'}, connection)
                    if temp_obj.image_1920:
                        get = self.create_images(prestashop, temp_obj.image_1920, product_data['prestashop_product_id'])
                    quantity = self.get_quantity(temp_obj.product_variant_ids[0], instance_id)
                    if float(quantity) > 0.0 :
                        get = self.update_quantity_prestashop(prestashop, product_data['prestashop_product_id'], quantity)
                        if get[0]==0:
                            error = str(get[1])
                    status = True
        return{
            'status' : status,
            'error' : error
        }
    
    def export_template(self, prestashop , template_data , instance_id , channel, connection):
        status = True
        error = ''
        prestashop_product_id = 0
        product_schema = False
        try:
            product_schema = prestashop.get('products', options = {'schema':'blank'})
        except Exception as e:
            status = False
            error = str(e)
        if product_schema:
            ps_categ_id = self.sync_categories(template_data.categ_id, instance_id, channel, connection)
            ps_extra_categ = []
            for j in template_data.connector_categ_ids.categ_ids:
                ps_ex_cat_id = self.sync_categories(j , instance_id, channel, connection )
                ps_extra_categ.append({'id':str(ps_ex_cat_id)})
            product_schema['product'].update({
                            'price': str(round(template_data.list_price,6)),
                            'active':'1',
                            'redirect_type':'404',
                            'minimal_quantity':'1',
                            'available_for_order':'1',
                            'show_price':'1',
                            'state':'1',
                            'default_on':'1',
                            'reference': str(template_data.default_code or ''),
                            'out_of_stock':'2',
                            'condition':'new',
                            'id_category_default':str(ps_categ_id),
                            'weight' : str(template_data.weight or ''),
                            'ean13': str(template_data.barcode or '')
                        })
            if template_data.standard_price:
                product_schema['product']['wholesale_price'] = str(round(template_data.standard_price,6))
            if type(product_schema['product']['name']['language']) == list:
                for i in range(len(product_schema['product']['name']['language'])):
                    product_schema['product']['name']['language'][i]['value'] = template_data.name
                    product_schema['product']['link_rewrite']['language'][i]['value'] = self._get_link_rewrite('', template_data.name)
                    product_schema['product']['description']['language'][i]['value'] = template_data.description
                    product_schema['product']['description_short']['language'][i]['value'] = template_data.description_sale
            else:
                product_schema['product']['name']['language']['value'] = template_data.name
                product_schema['product']['link_rewrite']['language']['value'] = self._get_link_rewrite('', template_data.name)
                product_schema['product']['description']['language']['value'] = template_data.description
                product_schema['product']['description_short']['language']['value'] = template_data.description_sale
            if type(product_schema['product']['associations']['categories']['category'])== list:
                product_schema['product']['associations']['categories']['category'] = product_schema['product']['associations']['categories']['category'][0]
            product_schema['product']['associations']['categories']['category']['id'] = str(ps_categ_id)
            pop_attr = product_schema['product']['associations'].pop('combinations',None)
            a1 = product_schema['product']['associations'].pop('images',None)
            a2 = product_schema['product'].pop('position_in_category',None)
            if ps_extra_categ:
                a3 = product_schema['product']['associations']['categories']['category'] = ps_extra_categ
            try:
                prestashop_product_id = prestashop.add('products', product_schema)
            except Exception as e:
                _logger.info("---exception raised while export template--- %r",product_schema)
                status = False
                error = str(e)
        return{
            'status': status,
            'error' : error,
            'prestashop_product_id':prestashop_product_id
            }

    def create_combination(self, prestashop , obj_pro , presta_main_product_id, instance_id):
        status = True
        prestashop_comb_id = 0
        error = ''
        combination_schema = False
        try:
            combination_schema = prestashop.get('combinations', options= {'schema':'blank'})
        except Exception as e:
            status = False
            error = str(e)
        if combination_schema:
            quantity = self.get_quantity(obj_pro, instance_id)
            image = obj_pro.image_1920
            if image:
                image_id = self.create_images(prestashop,image,presta_main_product_id)
                if image_id:
                    combination_schema['combination']['associations']['images']['image']['id'] = str(image_id)
            price_extra = float(obj_pro.lst_price) - float(obj_pro.list_price)
            presta_dim_list = []
            for value_id in obj_pro.product_template_attribute_value_ids:
                m_id = self.env['connector.option.mapping'].search([('odoo_id', '=', value_id.product_attribute_value_id.id),('instance_id','=', instance_id)])
                if m_id:
                    presta_dim_list.append({'id':str(m_id[0].ecomm_id)})
                else:
                    raise Warning('Please Map All Dimentions(Attributes and Attribute Values) First And than Try To Update Product')
            combination_schema['combination']['associations']['product_option_values']['product_option_value'] = presta_dim_list
            combination_schema['combination'].update({
                                    'ean13':obj_pro.barcode or '',
                                    'weight':str(obj_pro.weight or ''),
                                    'reference':obj_pro.default_code or '',
                                    'wholesale_price':str(round(obj_pro.standard_price,6)),
                                    'price':str(round(price_extra,6)),
                                    'quantity':quantity,
                                    'default_on':'0',
                                    'id_product':str(presta_main_product_id),
                                    'minimal_quantity':'1',
                                    })
            try:
                prestashop_comb_id = prestashop.add('combinations',combination_schema)
            except Exception as e:
                _logger.info("-exception_raised---creating combination -- adding_product_schema --%r",combination_schema)
                status = False
                error = str(e)
            if prestashop_comb_id:
                if float(quantity) > 0.0:
                    get = self.update_quantity_prestashop(prestashop, presta_main_product_id, quantity, None, prestashop_comb_id)
                    if get[0]==0:
                        status = False
                        error = str(get[1])
        return{
            'status': status,
            'error' : error,
            'prestashop_comb_id':prestashop_comb_id
        }
    

    def update_template(self, prestashop, product_data, tmpl_id, ecomm_id, ps_lang_id):
        status = False
        error = ''
        product_data['product']['price'] = str(round(tmpl_id.list_price,6))
        product_data['product']['wholesale_price'] = str(round(tmpl_id.standard_price,6))
        product_data['product']['weight'] = str(tmpl_id.weight or '')
        product_data['product']['reference'] = str(tmpl_id.default_code or '')
        product_data['product']['ean13'] = str(tmpl_id.barcode or '')
        if type(product_data['product']['name']['language']) == list:
            for i in range(len(product_data['product']['name']['language'])):
                presta_lang_id = product_data['product']['name']['language'][i]['attrs']['id']
                if presta_lang_id == str(ps_lang_id):
                    product_data['product']['name']['language'][i]['value'] = 	tmpl_id.name or ''
                    product_data['product']['description']['language'][i]['value'] = tmpl_id.description or ''
                    product_data['product']['description_short']['language'][i]['value'] = tmpl_id.description_sale or ''
        else:
            product_data['product']['name']['language']['value'] = tmpl_id.name or ''
            product_data['product']['description']['language']['value'] = tmpl_id.description or ''
            product_data['product']['description_short']['language']['value'] = tmpl_id.description_sale or ''
        a1 = product_data['product'].pop('position_in_category',None)
        a2 = product_data['product'].pop('manufacturer_name',None)
        a3 = product_data['product'].pop('quantity',None)
        a4 = product_data['product'].pop('type',None)
        try:
            returnid = prestashop.edit('products', ecomm_id, product_data)
        except Exception as e:
            _logger.info("----exception_raised-- while update_template %r",[ecomm_id,product_data])
            error = str(e)
        if returnid:
            status = True
            if 'image' not in product_data['product']['associations']['images']:
                if tmpl_id.image_1920:
                    get = self.create_images(prestashop, tmpl_id.image_1920, ecomm_id)
        return{
            'status':status,
            'error' : error
        }
          
    def _update_prestashop_specific_template(self, obj_pro_mapping, instance_id, channel, connection):
        prestashop = connection.get('prestashop' , connection)
        status = False
        error = ''
        tmpl_id = obj_pro_mapping.name
        ecomm_id =  obj_pro_mapping.ecomm_id
        returnid = False
        product_mapping  = self.env['connector.product.mapping']
        ps_lang_id =  connection.get('ps_lang_id',0)
        if prestashop:
            template_dic = self.update_template_category(prestashop, tmpl_id, ecomm_id , channel , instance_id, connection)
            if template_dic['status']:
                product_data = template_dic['product_data']
                update_temp = self.update_template(prestashop, product_data, tmpl_id, ecomm_id, ps_lang_id)
                if update_temp['status']:
                    returnid = update_temp['status']
                else:
                    error = update_temp['error']
            else:
                error = template_dic['error']
            if returnid:
                if tmpl_id.attribute_line_ids:
                    if not obj_pro_mapping.is_variants:
                        obj_pro_mapping.is_variants = True
                    for product_id in tmpl_id.product_variant_ids:
                        mapped_product_obj = product_mapping.search([('odoo_id','=', product_id.id),('instance_id','=', instance_id),('ecomm_combination_id','!=',0)])
                        if mapped_product_obj:
                            update_dictionary = self.update_product_combination(prestashop , product_id , mapped_product_obj.ecomm_combination_id , ecomm_id, instance_id)
                            if update_dictionary['status']:
                                mapped_product_obj.need_sync = 'No'
                                status = True
                            else:
                                error = update_dictionary ['error']
                        else:
                            combination_data = self.create_combination(prestashop , product_id ,ecomm_id , instance_id)
                            if combination_data['status']:
                                old_mapping = product_mapping.search([('ecomm_id','=',ecomm_id),('ecomm_combination_id','=',0),('instance_id','=',instance_id)])
                                if old_mapping:
                                    old_mapping.sudo().unlink()
                                    try:
                                        presta_mapping_data = prestashop.get('erp_product_merges' , options={'filter[prestashop_product_id]': ecomm_id , 'filter[prestashop_product_attribute_id]':0})
                                        if 'erp_product_merge' in presta_mapping_data['erp_product_merges']:
                                            mapping_id = presta_mapping_data['erp_product_merges']['erp_product_merge']['attrs']['id']
                                            prestashop.delete('erp_product_merges' , mapping_id)
                                    except:
                                        pass
                                self.create_odoo_connector_mapping('connector.product.mapping', 
                                            ecomm_id, 
                                            product_id.id, 
                                            instance_id,
                                            odoo_tmpl_id = tmpl_id.id,
                                            ecomm_combination_id = combination_data['prestashop_comb_id'],
                                            name = product_id.id
                                            )
                                self.create_ecomm_connector_mapping('connector.product.mapping',
                                                            'prestashop', 
                                                            {'odoo_id':product_id.id,
                                                            'ecomm_id':combination_data['prestashop_comb_id'],
                                                            'prod_tmpl_id':tmpl_id.id,
                                                            'presta_product_id': ecomm_id,
                                                            'created_by': 'odoo'}, connection)
                                status = True
                            else:
                                error = combination_data['error']
                else:
                    quantity = self.get_quantity(tmpl_id.product_variant_ids[0] , instance_id)
                    get = self.update_quantity_prestashop(prestashop, ecomm_id , quantity)
                    if get[0]==0:
                        error = str(get[1])
                    else:
                        status = True
                if status:
                    obj_pro_mapping.need_sync = 'No'
        return{
            'status' : status,
            'error' : error
        }
    

    @api.model
    def update_product_combination(self , prestashop , obj_pro , combination_id, presta_product_id, instance_id):
        status = True
        prestashop_comb_id = False
        error = ''
        combination_schema = False
        try:
            combination_schema = prestashop.get('combinations',combination_id)
        except Exception as e:
            status = False
            error = str(e)
        if combination_schema:
            quantity = self.get_quantity(obj_pro, instance_id)
      
            if obj_pro.image_1920:
                if not type(combination_schema['combination']['associations']['images']['image']) == list \
                   and 'id' not in combination_schema['combination']['associations']['images']['image']:
                    image_id = self.create_images(prestashop , obj_pro.image_1920 ,presta_product_id)
                    if image_id:
                        combination_schema['combination']['associations']['images']['image']['id'] = str(image_id)
            price_extra = float(obj_pro.lst_price) - float(obj_pro.list_price)
            presta_dim_list = []
            for value_id in obj_pro.product_template_attribute_value_ids:
                m_id = self.env['connector.option.mapping'].search([('odoo_id', '=', value_id.product_attribute_value_id.id),('instance_id','=', instance_id)])
                if m_id:
                    presta_dim_list.append({'id':str(m_id[0].ecomm_id)})
                else:
                    raise Warning('Please Map All Dimentions(Attributes and Attribute Values) First And than Try To Update Product')
            combination_schema['combination']['associations']['product_option_values']['product_option_value'] = presta_dim_list
            combination_schema['combination'].update({
                                    'ean13':obj_pro.barcode or '',
                                    'weight':str(obj_pro.weight or ''),
                                    'reference':obj_pro.default_code or '',
                                    'wholesale_price':str(round(obj_pro.standard_price,6)),
                                    'price':str(round(price_extra,6)),
                                    'quantity':quantity,
                                    'default_on':'0',
                                    'id_product':str(presta_product_id),
                                    'minimal_quantity':'1',
                                    })
            try:
                prestashop_comb_id = prestashop.edit('combinations', combination_id, combination_schema)
            except Exception as e:
                _logger.info("-----exception raised product_sync-update_prod_comb-%r",[combination_id,combination_schema])
                status = False
                error = str(e)
            if prestashop_comb_id:
                if float(quantity) > 0.0:
                    get = self.update_quantity_prestashop(prestashop, presta_product_id, quantity, None, combination_id)
                    if get[0]==0:
                        status = False
                        error = str(get[1])
        return{
            'status': status,
            'error' : error,
        } 
    
    @api.model
    def update_template_category(self, prestashop, template_data, presta_id , channel , instance_id, connection):
        status = True
        error = ''
        product_data = False
        try:
            product_data = prestashop.get('products', presta_id)
        except Exception as e:
            status = False
            error = str(e)
        if product_data:
            ps_categ_id = self.sync_categories(template_data.categ_id, instance_id, channel, connection)
            ps_extra_categ = []
            for j in template_data.connector_categ_ids.categ_ids:
                ps_ex_cat_id = self.sync_categories(j , instance_id, channel, connection )
                ps_extra_categ.append({'id':str(ps_ex_cat_id)})
            product_data['product'].update({'id_category_default':ps_categ_id})
            if ps_extra_categ:
                a2 = product_data['product']['associations']['categories']['category'] = ps_extra_categ
        return{
            'status' : status,
            'error' : error,
            'product_data' : product_data
            }

    @api.model
    def create_images(self, prestashop, image_data, resource_id, image_name=None, resource='images/products'):
        if image_name == None:
            image_name = 'op' + str(resource_id) + '.png'
        try:
            returnid = prestashop.add(str(resource) + '/' + str(resource_id), image_data, image_name)
            return returnid
        except Exception as e:
            return False


    def update_quantity_prestashop(self, prestashop, pid, quantity, stock_id=None, attribute_id=None):
        if attribute_id is not None:
            try:
                stock_search = prestashop.get('stock_availables', options={'filter[id_product]':pid, 'filter[id_product_attribute]':attribute_id})
            except Exception as e:
                return [0,' Unable to search given stock id', check_mapping[0]]
            if type(stock_search['stock_availables']) == dict:
                stock_id=stock_search['stock_availables']['stock_available']['attrs']['id']
                try:
                    stock_data = prestashop.get('stock_availables', stock_id)
                except Exception as e:
                    return [0, ' Error in Updating Quantity,can`t get stock_available data.']
                if type(quantity) == str:
                    quantity = quantity.split('.')[0]
                if type(quantity) == float:
                    quantity = int(quantity)
                stock_data['stock_available']['quantity'] = int(quantity)
                try:
                    up=prestashop.edit('stock_availables', stock_id, stock_data)
                except Exception as e:
                    pass
                return [1, '']
            else:
                return [0, ' No stock`s entry found in prestashop for given combination (Product id,Attribute id:)%r'%[pid,attribute_id]]
        if stock_id is None and attribute_id is None:
            try:
                product_data = prestashop.get('products', pid)
            except Exception as e:
                return [0,' Error in Updating Quantity,can`t get product data.']
            stock_id = product_data['product']['associations']['stock_availables']['stock_available']['id']
        if stock_id:
            try:
                stock_data = prestashop.get('stock_availables', stock_id)
            except Exception as e:
                return [0, ' Error in Updating Quantity,can`t get stock_available data.']
            except Exception as e:
                return [0, ' Error in Updating Quantity,%s'%str(e)]
            if type(quantity) == str:
                quantity = quantity.split('.')[0]
            if type(quantity) == float:
                quantity = quantity.as_integer_ratio()[0]
            stock_data['stock_available']['quantity'] = quantity
            try:
                up = prestashop.edit('stock_availables', stock_id, stock_data)
            except Exception as e:
                return [0, ' Error in Updating Quantity,Unknown Error.']
            except Exception as e:
                return [0, ' Error in Updating Quantity,Unknown Error.%s'%str(e)]
            return [1, '']
        else:
            return [0, ' Error in Updating Quantity,Unknown stock_id.']