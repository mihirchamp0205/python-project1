from django.shortcuts import render,redirect
from .models import User,Contact,Product,Wishlist,Cart,Transaction
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse


# Create your views here.

def validate_signup(request):
	email=request.GET.get('email')
	data={
		'is_taken':User.objects.filter(email__iexact=email).exists()
	}
	return JsonResponse(data)


def initiate_payment(request):
	user=User.objects.get(email=request.session['email'])
	try:
		amount = int(request.POST['amount'])       
	except:
		return render(request, 'pay.html', context={'error': 'Wrong Accound Details or amount'})

	transaction = Transaction.objects.create(made_by=user,amount=amount)
	transaction.save()
	merchant_key = settings.PAYTM_SECRET_KEY

	params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://localhost:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

	paytm_params = dict(params)
	checksum = generate_checksum(paytm_params, merchant_key)

	transaction.checksum = checksum
	transaction.save()
	carts=Cart.objects.filter(user=user,payment_status=False)
	for i in carts:
		i.payment_status=True
		i.save()
	carts=Cart.objects.filter(user=user,payment_status=False)
	request.session['cart_count']=len(carts)
	paytm_params['CHECKSUMHASH'] = checksum
	print('SENT: ', checksum)
	return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
	if request.method == 'POST':
		received_data = dict(request.POST)
		paytm_params = {}
		paytm_checksum = received_data['CHECKSUMHASH'][0]
		for key, value in received_data.items():
			if key == 'CHECKSUMHASH':
				paytm_checksum = value[0]
			else:
				paytm_params[key] = str(value[0])
        # Verify checksum
		is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
		if is_valid_checksum:
			received_data['message'] = "Checksum Matched"
		else:
			received_data['message'] = "Checksum Mismatched"
			return render(request, 'callback.html', context=received_data)
		return render(request, 'callback.html', context=received_data)


def index(request):
	try:
		user=User.objects.get(email=request.session['email'])
		if user.usertype=="user":
			return render(request,'index.html')
		else:
			return render(request,'seller_index.html')
	except:
		return render(request,'index.html')

def about(request):
	return render(request,'about.html')

def product(request):
	product=Product.objects.all()
	return render(request,'product.html',{'product':product})

def testimonial(request):
	return render(request,'testimonial.html')

def contact(request):
	return render(request,'contact.html')

def signup(request):
	if request.method=="POST":
		try:
			User.objects.get(email=request.POST['email'])
			msg="Email Already Exists"
			return render(request,'signup.html',{'msg':msg})
		except:
			if request.POST['password']==request.POST['cpassword']:
				User.objects.create(
						fname=request.POST['fname'],
						lname=request.POST['lname'],
						email=request.POST['email'],
						mobile=request.POST['mobile'],
						address=request.POST['address'],
						password=request.POST['password'],
						usertype=request.POST['usertype'],
						profile_pic=request.FILES['profile_pic']
					)
				msg="User Signup Successfully"
				return render(request,'login.html',{'msg':msg})
			else:
				msg="Password & Confirm Password Does Not Matched"
				return render(request,'signup.html',{'msg':msg})
	else:
		return render(request,'signup.html')

def login(request):
	if request.method=="POST":
		try:
			user=User.objects.get(email=request.POST['email'])
			if user.password==request.POST['password']:
				if user.usertype=="user":
					request.session['email']=user.email
					request.session['fname']=user.fname
					wishlists=Wishlist.objects.filter(user=user)
					request.session['whislist_count']=len(wishlists)
					carts=Cart.objects.filter(user=user,payment_status=False)
					request.session['cart_count']=len(carts)
					request.session['profile_pic']=user.profile_pic.url
					return render(request,'index.html')
				else:
					request.session['email']=user.email
					request.session['fname']=user.fname
					request.session['profile_pic']=user.profile_pic.url
					return render(request,'seller_index.html')
			else:
				msg="Password Is Incorrect"
				return render(request,'login.html',{'msg':msg})
		except Exception as e:
			print(e)
			msg="Email Is Not Registered"
			return render(request,'login.html',{'msg':msg})
	else:
		return render(request,'login.html')


def logout(request):
	try:
		del request.session['email']
		del request.session['fname']
		return render(request,'login.html')
	except:
		return render(request,'login.html')


def seller_index(request):
	return render(request,'seller_index.html')


def change_password(request):
	user=User.objects.get(email=request.session['email'])	
	if request.method=="POST":
		if user.password==request.POST['old_password']:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				msg="New Password & Confirm New Password Does Not Matched"
				if user.usertype=="seller":
					return render(request,'seller_change_password.html',{'msg':msg})
				else:
					return render(request,'change_password.html',{'msg':msg})

		else:
			msg="Old Password Does Not Matched"
			if user.usertype=="seller":
				return render(request,'seller_change_password.html',{'msg':msg})
			else:
				return render(request,'change_password.html',{'msg':msg})
	else:
		if user.usertype=="seller":
			return render(request,'seller_change_password.html')
		else:
			return render(request,'change_password.html')

def seller_add_product(request):
	if request.method=="POST":
		seller=User.objects.get(email=request.session['email'])
		Product.objects.create(
				seller=seller,
				product_company=request.POST['product_company'],
				product_name=request.POST['product_name'],
				product_model=request.POST['product_model'],
				product_price=request.POST['product_price'],
				product_desc=request.POST['product_desc'],
				product_image=request.FILES['product_image']
			)
		msg="Product Added Successfully"
		return render(request,'seller_add_product.html',{'msg':msg})
	else:
		return render(request,'seller_add_product.html')


def seller_view_product(request):
	seller=User.objects.get(email=request.session['email'])
	products=Product.objects.filter(seller=seller)
	return render(request,'seller_view_product.html',{'products':products})

def seller_edit_product(request,pk):
	product=Product.objects.get(pk=pk)
	if request.method=="POST":
		product.product_company=request.POST['product_company']
		product.product_name=request.POST['product_name']
		product.product_model=request.POST['product_model']
		product.product_price=request.POST['product_price']
		product.product_desc=request.POST['product_desc']
		try:
			product.product_image=request.FILES['product_image']
		except:
			pass
		product.save()
		msg="Product Updated Successfully"
		return render(request,'seller_edit_product.html',{'product':product,'msg':msg})
	else:
		return render(request,'seller_edit_product.html',{'product':product})


def seller_delete_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	return redirect('seller_view_product')


def add_to_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Wishlist.objects.create(user=user,product=product)
	#msg="Product Added To Wishlist Successfully"
	return redirect('wishlist')


def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=Wishlist.objects.filter(user=user)
	request.session['whislist_count']=len(wishlists)
	return render(request,'wishlist.html',{'wishlists':wishlists})

def product_details(request,pk):
	wishlist_flag=False
	cart_flag=False
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	try:
		Wishlist.objects.get(user=user,product=product)
		wishlist_flag=True
	except:
		pass
	try:
		Cart.objects.get(user=user,product=product,payment_status=False)
		cart_flag=True
	except:
		pass
	return render(request,'product_details.html',{'product':product,'wishlist_flag':wishlist_flag,'cart_flag':cart_flag})

def remove_from_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Wishlist.objects.get(user=user,product=product).delete()
	return redirect('wishlist')

def cart(request):
	net_price=0
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=False)
	for i in carts:
		net_price=net_price+i.total_price
	request.session['cart_count']=len(carts)
	return render(request,'cart.html',{'carts':carts,'net_price':net_price})

def remove_from_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.get(user=user,product=product).delete()
	return redirect('cart')

def add_to_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(
			user=user,
			product=product,
			product_price=product.product_price,
			product_qty=1,
			total_price=product.product_price,
			discount_price=product.product_price
		)
	return redirect('cart')

def change_qty(request,pk):
	cart=Cart.objects.get(pk=pk)
	product_qty=int(request.POST['product_qty'])
	cart.total_price=cart.discount_price*product_qty
	cart.product_qty=product_qty
	cart.save()
	return redirect('cart')

def myorder(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=True)
	return render(request,'myorder.html',{'carts':carts})


def discount(request,pk):
	cart=Cart.objects.get(pk=pk)
	discount=request.POST['discount']
	if cart.discount==discount:
		newprice=(cart.product_price*10)/100
		cart.discount_price=cart.discount_price-newprice
		cart.save()
		cart.total_price=cart.discount_price*cart.product_qty
		cart.save()
	return redirect('cart')

















