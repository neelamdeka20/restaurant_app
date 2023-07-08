from app import application
from flask import jsonify, Response, session
from app.models import *
from app import *
import uuid
import datetime
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import json

class APIResponse(Schema):
    message = fields.Str(default="Success")

class SignUpRequest(Schema):
    name = fields.Str(default = "Name")
    username = fields.Str(default = "username")
    password = fields.Str(default = "password")
    level = fields.Int(default = 0)

class LoginRequest(Schema):
    username = fields.Str(default="username")
    password = fields.Str(default="password")

class OrdersListResponse(Schema):
    orders = fields.List(fields.Dict())

class PlaceOrderRequest(Schema):
    order_id = fields.Str(default="order_id")

class AddItemRequest(Schema):
    item_id = fields.Str(default = "ID")
    item_name = fields.Str(default = "Name")
    calories_per_gm = fields.Int(default = 0)
    available_quantity = fields.Int(default = 0)
    restaurant_name = fields.Str(default = "Restaurant")
    unit_price = fields.Int(default = 0)

class ItemsListResponse(Schema):
    items = fields.List(fields.Dict())

class CreateItemOrderRequest(Schema):
    user_id = fields.Str(default = "user_id")
    item_id = fields.Str(default = "item_id")
    quantity = fields.Integer(default=0)

class ListOrdersByCustomerRequest(Schema):
    customer_id=fields.Str(default="customer id") 

class AddVendorRequest(Schema):
    user_id=fields.Str(default="user id")

#  Restful way of creating APIs through Flask Restful
class SignUpAPI(MethodResource, Resource):
    @doc(description='Sign Up API', tags=['SignUp API'])
    @use_kwargs(SignUpRequest, location=('json'))
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            user = User(
                uuid.uuid4(),
                kwargs['name'],
                kwargs['username'], 
                kwargs['password'], 
                kwargs['level'])
            db.session.add(user)
            db.session.commit()
            return APIResponse().dump(dict(message='User is successfully registered')), 200
        
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to register user : {str(e)}')), 400

api.add_resource(SignUpAPI, '/signup')
docs.register(SignUpAPI)


class LoginAPI(MethodResource, Resource):
    @doc(description='Login API', tags=['Login API'])
    @use_kwargs(LoginRequest, location=('json'))
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(username=kwargs['username'], password = kwargs['password']).first()
            if user:
                print('logged in')
                session['user_id'] = user.user_id
                print(f'User id : {str(session["user_id"])}')
                return APIResponse().dump(dict(message='User is successfully logged in')), 200
            else:
                return APIResponse().dump(dict(message='User not found')), 404
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to login user : {str(e)}')), 400
            

api.add_resource(LoginAPI, '/login')
docs.register(LoginAPI)


class LogoutAPI(MethodResource, Resource):
    @doc(description='Logout API', tags=['Logout API'])
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            if session['user_id']:
                session['user_id'] = None
                print('logged out')
                return APIResponse().dump(dict(message='User is successfully logged out')), 200
            else:
                print('user not found')
                return APIResponse().dump(dict(message='User is not logged in')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to logout user : {str(e)}')), 400            

api.add_resource(LogoutAPI, '/logout')
docs.register(LogoutAPI)


class AddVendorAPI(MethodResource, Resource):
    @doc(description="Add a vendor",tags=['add_vendor API'])
    @use_kwargs(AddVendorRequest,location=('json'))
    @marshal_with(APIResponse) # marshalling
    def post(self,**kwargs):
        try:
            if session['user_id']:
                user_id = kwargs['user_id']
                user_type=User.query.filter_by(user_id=user_id).first().level

                print(user_type)
                if(user_type ==0):
                    User.query.filter_by(user_id=user_id).update({User.level:1})
                    print(User.level)
                    db.session.commit()
                    return APIResponse().dump(dict(message="Customer is upgraded to vendor")),200
                else :
                    return APIResponse().dump(dict(message="Customer is already a vendor")),405
            else:
                return APIResponse().dump(dict(message="Customer is not logged in")),401
        except Exception as e :
            print(str(e))
            return  APIResponse().dump(dict(message=f"Not able to upgrade to vendor:  {str(e)}")),400
            
api.add_resource(AddVendorAPI, '/add_vendor')
docs.register(AddVendorAPI)


class GetVendorsAPI(MethodResource, Resource):
    @doc(description="Get vendors API", tags=['Vendors API'])
    @marshal_with(APIResponse)
    def get(self):
        try:
            if session['user_id']:
                vendors = []
                for vendor in User.query.filter_by(level=1).all():
                    items = []
                    for item in Item.query.filter_by(vendor_id=vendor.user_id).all():
                        items.append({"item_id": item.item_id, "item_name": item.item_name, "calories_per_gm": item.calories_per_gm, "available_quantity": item.available_quantity, "restaurant_name": item.restaurant_name, "unit_price": item.unit_price})
                    vendors.append({"vendor_id": vendor.user_id, "name": vendor.name, "items": items})
                return jsonify(vendors)
            else:
                return APIResponse().dump(dict(message="User is not logged in")), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f"Not able to list vendors: {str(e)}")), 400
           
api.add_resource(GetVendorsAPI, '/list_vendors')
docs.register(GetVendorsAPI)


class AddItemAPI(MethodResource, Resource):
    @doc(description="Add an item API",tags=['item API'])
    @use_kwargs(AddItemRequest,location=('json'))
    @marshal_with(APIResponse) # marshalling
    def post(self,**kwargs):
        try:
            if session['user_id']:
                user_id = session['user_id']
                user_type=User.query.filter_by(user_id=user_id).first().level
                print(user_id)
                if(user_type ==1):
                    item=Item(
                        kwargs['item_id'],
                        user_id,
                        kwargs['item_name'],
                        kwargs['calories_per_gm'],
                        kwargs['available_quantity'],
                        kwargs['restaurant_name'],
                        kwargs['unit_price']
                    )
                    db.session.add(item)
                    db.session.commit()
                    return APIResponse().dump(dict(message="Item is succesfully created")),200
                else :
                    return APIResponse().dump(dict(message="Logged in User is not a vendor")),405
            else:
                return APIResponse().dump(dict(message="Vendor is not logged in")),401
        except Exception as e :
            print(str(e))
            return  APIResponse().dump(dict(message=f"Not able to list vendors:  {str(e)}")),400

api.add_resource(AddItemAPI, '/add_item')
docs.register(AddItemAPI)


class ListItemsAPI(MethodResource, Resource):
    @doc(description='Items List API', tags=['Items API'])
    @marshal_with(ItemsListResponse)  # marshalling
    def get(self):
        try:
            if session['user_id']:
                    items = Item.query.all()
                    items_list = list()
                    for item in items:
                        item_dict = {}
                        item_dict['item_id'] = item.item_id
                        item_dict['vendor_id'] = item.vendor_id
                        item_dict['item_name'] = item.item_name
                        item_dict['restaurant_name'] = item.restaurant_name
                        item_dict['unit_price'] = item.unit_price
    
                        items_list.append(item_dict)
                    print(items_list)
                    return ItemsListResponse().dump(dict(items=items_list)), 200
            else:
                print('User is not logged in')
                return APIResponse().dump(dict(message='User is not logged in')), 401
        except Exception as e:
            return APIResponse().dump(dict(message = f"Not able to list items : {str(e)}")), 400

api.add_resource(ListItemsAPI, '/list_items')
docs.register(ListItemsAPI)


class CreateItemOrderAPI(MethodResource, Resource):
    @doc(description="Create Item Order API",tags=['CreateItemOrder API'])
    @use_kwargs(CreateItemOrderRequest,location=('json'))
    @marshal_with(APIResponse) 
    def post(self,**kwargs):
        try:
            user_id = kwargs['user_id']
            item_id = kwargs['item_id']
            quantity = kwargs['quantity']
            user = User.query.filter_by(user_id=user_id).first()
            item = Item.query.filter_by(item_id=item_id).first()
            if not user:
                return APIResponse().dump(dict(message="Invalid user_id")),400
            if not item:
                return APIResponse().dump(dict(message="Invalid item_id")),400

            if quantity > item.available_quantity:
                return APIResponse().dump(dict(message="Requested quantity is not available")),400
            order_id = str(uuid.uuid1())
            order = Order(order_id, user_id)
            db.session.add(order)
            db.session.commit()
            id = str(uuid.uuid4())
            order_item = OrderItems(id, order_id, item_id, quantity)
            db.session.add(order_item)
            item.available_quantity = item.available_quantity - quantity
            db.session.commit()
            return APIResponse().dump(dict(message="Order created successfully")),200
        except Exception as e:
            return APIResponse().dump(dict(message = 'Not able to create items order')), 400

api.add_resource(CreateItemOrderAPI, '/create_items_order')
docs.register(CreateItemOrderAPI)


class PlaceOrderAPI(MethodResource, Resource):
    @doc(description="Place Order API",tags=['PlaceOrder API'])
    @use_kwargs(PlaceOrderRequest,location=('json'))
    @marshal_with(APIResponse) 
    def post(self,**kwargs):
        try:
            order_id=kwargs['order_id']
            user = User.query.filter_by(user_id=session['user_id']).first()
            if not user:
                return APIResponse().dump(dict(message="You must be logged in to place an order.")),401
            order = Order.query.filter_by(order_id=order_id).first()
            if order:
                Order.query.filter_by(order_id=order_id).update({Order.is_placed:1})

                db.session.commit()
                return APIResponse().dump(dict(message="Order placed successfully.")),201
            else:
                return APIResponse().dump(dict(message="Items not added.")),405
        except Exception as e:
            return APIResponse().dump(dict(message = f'Not able to place order : {str(e)}')), 400

api.add_resource(PlaceOrderAPI, '/place_order')
docs.register(PlaceOrderAPI)


class ListOrdersByCustomerAPI(MethodResource, Resource):
    @doc(description="List Order API by Customer",tags=['list_order_by_customer API'])
    @use_kwargs(ListOrdersByCustomerRequest,location=('json'))
    @marshal_with(OrdersListResponse) 
    def post(self, **kwargs):
        try:
            customer_id=kwargs['customer_id']
            print(customer_id)
            user = User.query.filter_by(user_id=session['user_id']).first()
            print(user)
            if not user:
                return APIResponse().dump(dict(message="You must be logged in to view your orders.")),401

            order = Order.query.filter_by(user_id=customer_id).all()
            print(order)
            if not order:
                return APIResponse().dump(dict(message="No orders found for this customer.")),404 
            order_list = list()
            for order in order:
                order_dict = {}
                order_dict['order_id'] = order.order_id
                order_dict['user_id'] = order.user_id
                order_dict['total_amount'] = order.total_amount
                order_dict['is_placed'] = order.is_placed
                order_list.append(order_dict)
            print(order_list)
            return OrdersListResponse().dump(dict(orders=order_list)), 200
        except Exception as e:
            return APIResponse().dump(dict(message = 'Not able to list orders')), 400
            
api.add_resource(ListOrdersByCustomerAPI, '/list_orders')
docs.register(ListOrdersByCustomerAPI)


class ListAllOrdersAPI(MethodResource, Resource):
    @doc(description='Orders List API', tags=['ListAllOrders API'])
    @marshal_with(OrdersListResponse)  # marshalling
    def get(self):
        try:
            user = User.query.filter_by(user_id=session['user_id']).first()
            if not user or user.level != 2:
                return APIResponse().dump(dict(message="You must be an admin to view all orders.")),401
            orders = Order.query.all()
            if not orders:
                return APIResponse().dump(dict(message="No orders found.")),404
            orders_list = list()
            for order in orders:
                order_dict = {}
                order_dict['order_id'] = order.order_id
                order_dict['user_id'] = order.user_id
                order_dict['total_amount'] = order.total_amount
 
                orders_list.append(order_dict)
            print(orders_list)
            return OrdersListResponse().dump(dict(orders=orders_list)), 200
        except Exception as e:
            return APIResponse().dump(dict(message = 'Not able to list orders')), 400
            
api.add_resource(ListAllOrdersAPI, '/list_all_orders')
docs.register(ListAllOrdersAPI)