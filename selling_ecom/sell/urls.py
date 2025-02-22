from django.urls import path
from . import views
from .views import update_cart_item_quantity

urlpatterns = [
    path('',views.index,name='index'),
    path('about/',views.about,name='about'),
    path('blog-details/',views.blogdetails,name='blog-details'),
    path('blog/',views.blog,name='blog'),
    path('contact/',views.contact,name='contact'),
    path('product-details/',views.productdetails,name='product-details'),
    path('product/',views.product,name='product'),
    path('shopping-cart/',views.shopingcart,name='shoping-cart'),
    path('wishlist/', views.wishlist,name='wishlist'),
    path('productshop/', views.Productshop,name='product_shop'),
    path('view_order', views.vieworder,name="view_order"),



    path('login/',views.LoginView,name='login'),
    path('register/',views.register_view,name='register'),
    path('seller-register/',views.seller_register_view,name='seller_register'),
    path('logout/',views.logout_view,name='logout'),

    path('users/', views.user_list, name='user_list'),
    path('send_message/<int:user_id>/', views.send_message, name='send_message'),
    path('conversation/<int:user_id>/', views.view_conversation, name='view_conversation'),
    path('message_user/<int:user_id>/', views.message_user, name='message_user'),


    path('add-to-cart/<int:product_id>/',views.add_to_cart,name='add'),
    path('product-detail/<int:product_id>/', views.product_detail, name='product_detail'),
    path('checkout', views.checkout,name='checkout'),
    path('remove/<int:cart_item_id>/',views.remove_from_cart,name='remove'),
    path('remove/product/<int:id>/',views.remove_product,name='remove_product'),

    path('start_order/', views.start_order,name='start_order'),
    path('shop/<str:category>/', views.gencategory, name='gencategory'),

    path('address/', views.address,name="address"),
    path('update-cart-item-quantity/', update_cart_item_quantity, name='update_cart_item_quantity'),



    path('admin-consumer', views.adminconsumer,name='admin_consumer'),
    path('admin-farmer', views.adminfarmer,name='admin_farmer'),
    path('admin-order', views.adminorder,name='admin_order'),
    path('admin-product', views.adminproduct,name='admin_product'),
]