from django.shortcuts import render,redirect
from django.contrib import messages
from .models import Product,Cart,CartItem,CustomUser,OrderItem,Order,Category,Address,Material
from django.http import HttpResponseRedirect

from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,get_object_or_404,redirect

from django.contrib.auth import logout
from django.contrib.auth import authenticate,login
from django.contrib.auth import update_session_auth_hash

from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

from django.db.models import Q
from django.http import HttpResponse
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.http import Http404

from .models import Address, CartItem
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order, OrderItem 
# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from django.conf import settings



# Create your views here.


def index(request):
    if hasattr(request.user, 'is_farmer') and request.user.is_farmer:
        product = Product.objects.filter(user=request.user)
    else:
        product = Product.objects.all()

    category_obj = Category.objects.all()
    material_obj = Material.objects.all()
    sort_option = request.GET.get('sorted')
    search = request.GET.get('search')
    categories = request.GET.getlist('category')
    materials = request.GET.getlist('material')

    if sort_option == '2':
        product = product.order_by('-price')
    elif sort_option == '3':
        product = product.order_by('price')

    if search:
        product = product.filter(Q(name__icontains=search) | Q(category__name__icontains=search))
    
    if categories:
        product = product.filter(category__name__in=categories)
    
    if materials:
        product = product.filter(material__name__in=materials)

    total_cart_items = 0
    total_message_items = 0
    total_price = 0
    cart_items = []

    if request.user.is_authenticated:
        total_message_items = Messageing.objects.filter(recipient=request.user, is_read=False).count()
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_cart_items = cart_items.count()

        for cart_item in cart_items:
            cart_item.total_price = cart_item.product.price * cart_item.quantity
            total_price += cart_item.total_price

    total_amount = sum(cart_item.total_price for cart_item in cart_items) if cart_items else 0

    context = {
        'product': product,
        'total_amount': total_amount,
        'search': search,
        'category_obj': category_obj,
        'material_obj': material_obj,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'total_message_items': total_message_items,
    }
    return render(request, 'index.html', context)
@login_required
def product_detail(request, product_id):
    
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_cart_items = cart_items.count()
    product = get_object_or_404(Product, id=product_id)

    total_cart_items = 0
    total_message_items = 0
    total_price = 0
    cart_items = []

    if request.user.is_authenticated:
        total_message_items = Messageing.objects.filter(recipient=request.user, is_read=False).count()
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_cart_items = cart_items.count()

        for cart_item in cart_items:
            cart_item.total_price = cart_item.product.price * cart_item.quantity
            total_price += cart_item.total_price

    total_amount = sum(cart_item.total_price for cart_item in cart_items) if cart_items else 0

    context = {
        'product': product,
        'total_amount': total_amount,
        # 'search': search,
        # 'category_obj': category_obj,
        # 'material_obj': material_obj,
        'total_price': total_price,
        'product': product,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'total_message_items': total_message_items,
    }
            


    return render(request, 'product-detail.html',context)

@login_required
def message_product_owner(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = product.user  # Assuming user field represents the owner
            message.save()
            return redirect('view_conversation', user_id=product.user.id)
    else:
        form = MessageForm()
    return render(request, 'send_message.html', {'form': form, 'recipient': product.user})

def remove_from_cart(request,cart_item_id):
    cart_item=get_object_or_404(CartItem,id=cart_item_id)
    cart_item.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def remove_product(request,id):
    cart_item=get_object_or_404(Product,id=id)
    cart_item.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
    else:
        cart_item.quantity += 1

    cart_item.save()
    messages.success(request, 'Product added to the cart')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def checkout(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None  # Handle case where no address exists for the user

    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_price = 0
    total_discount = 0
    speed_delivery = 16
    normal_delivery = 0
    total_cart_items = cart_items.count()

    # Calculate discounts and total price
    for cart_item in cart_items:
        product_discount = cart_item.product.discount or 0  # Ensure there's a fallback if discount is None
        product_price = cart_item.product.price or 0  # Ensure there's a fallback if price is None
        cart_item.total_discount = product_discount * cart_item.quantity
        total_discount += cart_item.total_discount
        cart_item.total_price = product_price * cart_item.quantity
        total_price += cart_item.total_price

    
    total_amount = total_price - total_discount
    discounted_amount = total_amount
    final_amount_with_speed = discounted_amount + speed_delivery

    # Populate form data based on whether an address exists
    form_data = {
        'first_name': address.first_name if address else '',
        'last_name': address.last_name if address else '',
        'email': address.email if address else '',
        'address': address.address if address else '',
        'zipcode': address.zipcode if address else '',
    }

    context = {
        'cart_items': cart_items,
        'address': address,
        'form_data': form_data,
        'total_price': total_price,
        'total_discount': total_discount,
        'total_cart_items': total_cart_items,
        'total_amount': total_amount,
        'discounted_amount': discounted_amount,
        'final_amount_with_speed': final_amount_with_speed,
        'speed_delivery': speed_delivery,
        'normal_delivery': normal_delivery
    }
    return render(request, 'checkout.html', context)


def start_order(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        shipping_option = request.POST.get('shipping-option', 'Standard Delivery')

        # Convert float to Decimal
        speed_delivery_cost = Decimal('16.00') if shipping_option == 'Speed Delivery' else Decimal('0.00')

        # Fetch the cart associated with the current user
        user_cart = Cart.objects.filter(user=request.user).first()
        if not user_cart:
            messages.error(request, "No cart found for this user.")
            return redirect('cart')

        cart_items = CartItem.objects.filter(cart=user_cart)
        if not cart_items.exists():
            messages.error(request, "No items in cart.")
            return redirect('cart')

        # Calculating total price from cart items using Decimal for all arithmetic
        total_price = sum(Decimal(item.product.price) * item.quantity for item in cart_items)
        total_discount = sum(Decimal(item.product.discount) * item.quantity for item in cart_items)
        total_cost = total_price - total_discount + speed_delivery_cost

        # Create Order
        try:
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                address=address,
                zipcode=zipcode,
                shipping_method=shipping_option,
                shipping_cost=speed_delivery_cost,
                total_cost=total_cost
            )
            # messages.success(request, "Order created successfully!")

            # Create OrderItems and update product stock
            for item in cart_items:
                product = item.product
                if product.stock_quantity >= item.quantity:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=Decimal(product.price) * item.quantity,
                        quantity=item.quantity,
                    )
                    # Update product stock quantity
                    product.stock_quantity -= item.quantity
                    product.save()
                else:
                    messages.warning(request, f"Not enough stock for product: {product.name}")
                    return redirect('shoping-cart')

            # Clear the cart
            cart_items.delete()
            # messages.success(request, "Order placed successfully!")
            return redirect('wishlist')
        except Exception as e:
            messages.error(request, f"An error occurred while placing the order: {e}")
            return redirect('shoping-cart')

    return render(request, 'shoping-cart.html')


def wishlist(request):
    return render(request, 'payment.html')
    
def Productshop(request):
    product = Product.objects.all()
    cart_items = CartItem.objects.all()
    total_cart_items = cart_items.count()
    category_obj=Category.objects.all()
    material_obj=Material.objects.all()
    sort_option=request.GET.get('sorted')
    search = request.GET.get('search')
    categories = request.GET.getlist('category') # Update the parameter name here to 'amentities'
    materials = request.GET.getlist('material') # Update the parameter name here to 'amentities'

    if sort_option == '2':  # High Price → Low Price
        product = product.order_by('-price')
    elif sort_option == '3':  # Low Price → High Price
        product = product.order_by('price')

    if search:
        product = product.filter(
            Q(name__icontains=search)|
            Q(category__name__icontains=search)
        )
    
    if categories:
        product = product.filter(category__name__in=categories)
        
    if materials:
        product = product.filter(material__name__in=materials)
        

    total_cart_items = 0
    total_message_items = 0
    total_price = 0
    cart_items = []

    if request.user.is_authenticated:
        total_message_items = Messageing.objects.filter(recipient=request.user, is_read=False).count()
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_cart_items = cart_items.count()

        for cart_item in cart_items:
            cart_item.total_price = cart_item.product.price * cart_item.quantity
            total_price += cart_item.total_price

    total_amount = sum(cart_item.total_price for cart_item in cart_items) if cart_items else 0

    context = {
        'product': product,
        'category_obj': category_obj,
        'material_obj': material_obj,
        'total_price': total_price,
        'total_amount': total_amount,
        'cart_items': cart_items,
        'total_message_items': total_message_items,
        'total_cart_items': total_cart_items,
        'search': search,
        'categories': categories,  # Add this count to the context
    }
    return render(request, 'product-shop.html',context)


@login_required
def address(request):
    try:
        address = Address.objects.get(user=request.user)  # Get the unique address for the user
    except Address.DoesNotExist:
        address = None  # If no address exists, set address to None

    if request.method == "POST":
        # Fetch data from form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address_field = request.POST.get('address')  # Avoid name conflict with 'address' variable
        zipcode = request.POST.get('zipcode')

        if address:
            # Update existing address
            address.first_name = first_name
            address.last_name = last_name
            address.email = email
            address.address = address_field
            address.zipcode = zipcode
            address.save()
            messages.success(request, 'Address updated successfully!')
        else:
            # Create new address if none exists
            Address.objects.create(user=request.user, first_name=first_name, last_name=last_name, email=email, address=address_field, zipcode=zipcode)
            messages.success(request, 'Address added successfully!')

        return redirect('address')  # Redirect to the same page to avoid resubmission of form

    # Prepare form data if address exists; otherwise, use empty strings
    form_data = {
        'first_name': address.first_name if address else '',
        'last_name': address.last_name if address else '',
        'email': address.email if address else '',
        'address': address.address if address else '',
        'zipcode': address.zipcode if address else '',
    }

    return render(request, 'address.html', {'address': address, 'form_data': form_data})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def update_cart_item_quantity(request):
    cart_item_id = request.POST.get('cart_item_id')
    new_quantity = int(request.POST.get('quantity'))

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart__user=request.user)
        cart_item.quantity = new_quantity
        cart_item.save()

        total_price = 0
        total_discount = 0

        cart_items = CartItem.objects.filter(cart__user=request.user)
        for item in cart_items:
            item.total_discount = item.product.discount * item.quantity
            total_discount += item.total_discount
            item.total_price = item.product.price * item.quantity
            total_price += item.total_price

        discounted_amount = total_price - total_discount

        response_data = {
            'success': True,
            'product_id': cart_item.product.id,
            'new_total_price': cart_item.total_price,
            'total_price': total_price,
            'discounted_amount': discounted_amount
        }
        return JsonResponse(response_data)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'CartItem does not exist'})

@login_required
def shopingcart(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_price = 0
    total_discount = 0
    total_cart_items = cart_items.count()
   

    
# add the cart items
    for cart_item in cart_items: 
        cart_item.total_discount = cart_item.product.discount * cart_item.quantity
        total_discount += cart_item.total_discount

    for cart_item in cart_items: 
        cart_item.total_price = cart_item.product.price * cart_item.quantity
        total_price += cart_item.total_price
    
    total_amount = sum(cart_item.total_price for cart_item in cart_items)
    discounted_amount=total_amount-total_discount

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_discount': total_discount,
        'total_cart_items': total_cart_items,
        'total_amount': total_amount,
        'discounted_amount': discounted_amount,
    }
    return render(request,'shoping-cart.html',context)

def about(request):
    return render(request,'about.html')

def blogdetails(request):
    return render(request,'index.html')

def blog(request):
    return render(request,'blog-detail.html')

def contact(request):
    return render(request,'contact.html')

def productdetails(request):

    return render(request,'product-detail.html')



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Category, Product, Material

def product(request):
    if request.method == 'POST':
        if 'material_name' in request.POST:  # Handling material Creation
            material_name = request.POST.get('material_name')
            if not Material.objects.filter(name=material_name).exists():
                Material.objects.create(name=material_name)
                messages.success(request, 'Material Created Successfully!')
            else:
                messages.error(request, 'Category already exists.')

        elif 'category_name' in request.POST:  # Handling Category Creation
            category_name = request.POST.get('category_name')
            if not Category.objects.filter(name=category_name).exists():
                Category.objects.create(name=category_name)
                messages.success(request, 'Category Created Successfully!')
            else:
                messages.error(request, 'Category already exists.')
        
        elif 'product_name' in request.POST:  # Handling Product Creation
            product_name = request.POST.get('product_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category_name = request.POST.get('category')
            material_name = request.POST.get('materials')
            discount = request.POST.get('discount', 0)  # Set default discount to 0 if not provided
            stock_quantity = request.POST.get('stock_quantity')
            size = request.POST.get('size')
            gender = request.POST.get('gender')
            image = request.FILES.get('image')

            category = Category.objects.get(name=category_name)  # Assumes category must already exist
            material = Material.objects.get(name=material_name)  # Assumes material must already exist

            # Ensure discount is converted to a numeric value, or set to 0 if empty
            try:
                discount = float(discount) if discount else 0
            except ValueError:
                discount = 0

            Product.objects.create(
                user=request.user,
                name=product_name,
                description=description,
                price=price,
                category=category,
                material=material,
                discount=discount,
                stock_quantity=stock_quantity,
                size=size,
                gender=gender,
                image=image
            )
            messages.success(request, 'Product Created Successfully!')
        
        return redirect('product')
    
    categories = Category.objects.all()
    materials = Material.objects.all()
    products = Product.objects.filter(user=request.user)
    return render(request, 'product.html', {'categories': categories, 'materials': materials, 'products': products})

def gencategory(request, category):
    if category in ['men', 'women', 'accessories']:
        product = Product.objects.filter(gender=category)
    else:
        product = Product.objects.all()
    
    context = {
        'product': product,
    }

    return render(request, 'gendershop.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Messageing
from .forms import MessageForm
from .models import CustomUser


@login_required
def view_conversation(request, user_id):
    recipient = get_object_or_404(CustomUser, id=user_id)
    messages = Messageing.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).order_by('timestamp')

    # Mark all messages as read
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'view_conversation.html', {'messages': messages, 'recipient': recipient})

@login_required
def user_list(request):
    # Get users involved in messages with the current user
    messages = Messageing.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    user_ids = set(messages.values_list('sender_id', flat=True)) | set(messages.values_list('recipient_id', flat=True))
    user_ids.discard(request.user.id)  # Remove the current user's ID if present

    # Get unique users involved in the conversations
    users = CustomUser.objects.filter(id__in=user_ids)

    # Add unread message count for each user
    unread_messages = {}
    for user in users:
        unread_messages[user.id] = Messageing.objects.filter(recipient=request.user, sender=user, is_read=False).exists()

    return render(request, 'user_list.html', {'users': users, 'unread_messages': unread_messages})

@login_required
def send_message(request, user_id=None):
    recipient = None
    
    # Check if user_id is provided
    if user_id:
        recipient = get_object_or_404(CustomUser, id=user_id)

    if recipient:
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                message.recipient = recipient
                message.save()
                return redirect('view_conversation', user_id=recipient.id)
        else:
            form = MessageForm(initial={'recipient': recipient})
        return render(request, 'send_message.html', {'form': form, 'recipient': recipient})
    else:
        return render(request, 'error_page.html', {'error_message': 'Recipient not found'})

@login_required
def message_user(request, user_id):
    recipient = get_object_or_404(CustomUser, id=user_id)
    existing_messages = Messageing.objects.filter(sender=request.user, recipient=recipient) | \
                        Messageing.objects.filter(sender=recipient, recipient=request.user)

    if existing_messages.exists():
        return redirect('view_conversation', user_id=user_id)
    else:
        form = MessageForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('view_conversation', user_id=user_id)
        return render(request, 'send_message.html', {'form': form, 'recipient': recipient})


def logout_view(request):
    logout(request)
    return redirect(index)

def LoginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = CustomUser.objects.filter(username=username).first()

        if not user_obj:
            messages.warning(request, 'Account not found')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        user_authenticated = authenticate(request, username=username, password=password)

        if not user_authenticated:
            messages.warning(request, 'Invalid password')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        print(f"Authenticated User: {user_authenticated}")

        login(request, user_authenticated)
        return redirect('/')

    return render(request, 'login.html')

def seller_register_view(request):
    if request.method == 'POST':
        firstname=request.POST.get('firstname')
        lastname=request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if a user with the provided email already exists
        user_exists = CustomUser.objects.filter(email=email).exists()

        if user_exists:
            messages.warning(request, 'User with this email already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Create a new CustomUser
        user = CustomUser.objects.create(username=username, email=email,first_name=firstname,last_name=lastname,is_farmer=True)
        user.set_password(password)
        user.save()

        # Redirect to the login page
        return redirect('login')

    # If the request method is not POST, render the registration page
    return render(request, 'seller_register.html')

def register_view(request):
    if request.method == 'POST':
        firstname=request.POST.get('firstname')
        lastname=request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if a user with the provided email already exists
        user_exists = CustomUser.objects.filter(email=email).exists()

        if user_exists:
            messages.warning(request, 'User with this email already exists')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Create a new CustomUser
        user = CustomUser.objects.create(username=username, email=email,first_name=firstname,last_name=lastname)
        user.set_password(password)
        user.save()

        # Redirect to the login page
        return redirect('login')

    # If the request method is not POST, render the registration page
    return render(request, 'register.html')
@login_required
def vieworder(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('action')

        if order_id:
            order = get_object_or_404(OrderItem, pk=order_id)
            if new_status in [status[0] for status in OrderItem.STATUS_CHOICES]:  # Check if new status is valid
                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to {new_status}.")
                return redirect('view_order')  # Make sure this matches your URL name
        else:
            messages.error(request, "Order ID not provided.")

    # For buyers: List OrderItems linked to Orders made by the user
    buyer_orders = OrderItem.objects.filter(order__user=request.user).order_by('-created_at')

    # For sellers: List OrderItems linked to Products managed by the user
    seller_orders = OrderItem.objects.filter(product__user=request.user).order_by('-created_at')
    

    total_cart_items = 0
    total_message_items = 0
    total_price = 0
    cart_items = []

    if request.user.is_authenticated:
        total_message_items = Messageing.objects.filter(recipient=request.user, is_read=False).count()
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_cart_items = cart_items.count()

        for cart_item in cart_items:
            cart_item.total_price = cart_item.product.price * cart_item.quantity
            total_price += cart_item.total_price

    total_amount = sum(cart_item.total_price for cart_item in cart_items) if cart_items else 0

    context = {
        'product': product,
        'total_amount': total_amount,
        # 'search': search,
        # 'category_obj': category_obj,
        # 'material_obj': material_obj,
        'total_price': total_price,
        'product': product,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'cart_items': cart_items,
        'total_cart_items': total_cart_items,
        'buyer_orders': buyer_orders,
         'seller_orders': seller_orders,
         'cart_items': cart_items,
         'total_cart_items': total_cart_items,
        'total_message_items': total_message_items,
    }
            

    

    return render(request, 'order-page.html',context)


def admindash(re):
    product = Product.objects.filter(user_id=re.user)
    return render(re,'my_products.html',{'product': product})

def adminfarmer(re):
    # Check if the user is a farmer
    if re.user.is_farmer:
        farmer = CustomUser.objects.all()  # Get all users (assuming you want to see all users if the admin is a farmer)
    else:
        farmer = CustomUser.objects.filter(is_farmer=True)  # Get only users who are farmers

    return render(re, 'admin_view_farmer.html', {'farmer': farmer})


def adminconsumer(re):
    farmer = CustomUser.objects.all()
    return render(re,'admin_view_cunsumer.html', {'farmer': farmer})

def adminproduct(re):
    product=Product.objects.all().order_by('-created_at')
    return render(re,'admin_view_product.html',{'product': product})

def adminorder(re):
    order=OrderItem.objects.all().order_by('-created_at')
    return render(re,'admin_view_order.html',{'order': order})