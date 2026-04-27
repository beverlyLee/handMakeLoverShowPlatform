const { getProductDetail } = require('../../api/products');
const { getAddressList } = require('../../api/users');
const { createOrder } = require('../../api/orders');
const { getMyCoupons, SHIPPING_METHODS, PAY_METHODS } = require('../../api/promotions');
const { showToast, showLoading, hideLoading } = require('../../utils/util');
const storage = require('../../utils/storage');

Page({
  data: {
    productId: null,
    product: null,
    quantity: 1,
    selectedAddress: null,
    remark: '',
    isLoading: true,
    isSubmitting: false,

    formattedProductPrice: '0.00',
    formattedProductAmount: '0.00',
    formattedDiscountAmount: '0.00',
    formattedShippingFee: '0.00',
    formattedPayAmount: '0.00',

    availableCoupons: [],
    selectedCoupon: null,
    showCouponPicker: false,

    shippingMethods: SHIPPING_METHODS,
    selectedShipping: SHIPPING_METHODS[0],
    showShippingPicker: false,

    payMethods: PAY_METHODS,
    selectedPayMethod: PAY_METHODS[0],
    showPayMethodPicker: false,

    productAmount: 0,
    discountAmount: 0,
    shippingFee: 0,
    payAmount: 0,

    estimatedArrivalDate: '',

    showMoreOptions: false
  },

  onLoad(options) {
    console.log('订单确认页面加载', options);
    this.initTestToken();

    const productId = options.id;
    if (!productId) {
      showToast('参数错误');
      wx.navigateBack();
      return;
    }

    this.setData({ 
      productId: parseInt(productId),
      quantity: options.quantity ? parseInt(options.quantity) : 1
    });

    this.loadPageData();
    this.calculateEstimatedArrival();
  },

  initTestToken() {
    const currentToken = storage.getToken();
    if (!currentToken) {
      storage.setToken('test_token');
      console.log('已设置测试 Token');
    }
  },

  calculateEstimatedArrival() {
    const today = new Date();
    const days = this.data.selectedShipping.estimatedDays;
    const arrivalDate = new Date(today);
    arrivalDate.setDate(today.getDate() + days);
    
    const year = arrivalDate.getFullYear();
    const month = String(arrivalDate.getMonth() + 1).padStart(2, '0');
    const day = String(arrivalDate.getDate()).padStart(2, '0');
    
    this.setData({
      estimatedArrivalDate: `${year}年${month}月${day}日`
    });
  },

  async loadPageData() {
    this.setData({ isLoading: true });

    try {
      await Promise.all([
        this.loadProductDetail(),
        this.loadDefaultAddress(),
        this.loadAvailableCoupons()
      ]);
    } catch (error) {
      console.error('加载页面数据失败:', error);
    } finally {
      this.setData({ isLoading: false });
    }
  },

  async loadProductDetail() {
    try {
      const product = await getProductDetail(this.data.productId);
      this.setData({ product: product });
      this.updateFormattedAmounts();
    } catch (error) {
      console.error('加载商品详情失败:', error);
      showToast('加载商品失败');
    }
  },

  async loadAvailableCoupons() {
    try {
      const productAmount = this.data.product ? this.data.product.price * this.data.quantity : 0;
      
      const result = await getMyCoupons({ 
        status: 'available',
        order_amount: productAmount
      });
      
      const coupons = result?.coupons || result?.list || [];
      
      const availableCoupons = coupons.filter(uc => {
        if (uc.status !== 'unused') return false;
        if (!uc.coupon) return false;
        if (uc.coupon.can_apply === false) return false;
        return true;
      });
      
      const formattedCoupons = availableCoupons.map(uc => ({
        ...uc.coupon,
        user_coupon_id: uc.id,
        calculated_discount: uc.coupon.calculated_discount || 0
      }));
      
      this.setData({ availableCoupons: formattedCoupons });
    } catch (error) {
      console.error('加载优惠券失败:', error);
    }
  },

  updateFormattedAmounts() {
    const product = this.data.product;
    const quantity = this.data.quantity;
    const selectedCoupon = this.data.selectedCoupon;
    const selectedShipping = this.data.selectedShipping;
    
    if (!product) {
      this.setData({
        formattedProductPrice: '0.00',
        formattedProductAmount: '0.00',
        formattedDiscountAmount: '0.00',
        formattedShippingFee: '0.00',
        formattedPayAmount: '0.00',
        productAmount: 0,
        discountAmount: 0,
        shippingFee: 0,
        payAmount: 0
      });
      return;
    }
    
    const productAmount = product.price * quantity;
    const shippingFee = selectedShipping ? selectedShipping.fee : 0;
    const discountAmount = selectedCoupon ? (selectedCoupon.calculated_discount || 0) : 0;
    const payAmount = Math.max(productAmount - discountAmount + shippingFee, 0);
    
    this.setData({
      formattedProductPrice: product.price.toFixed(2),
      formattedProductAmount: productAmount.toFixed(2),
      formattedDiscountAmount: discountAmount.toFixed(2),
      formattedShippingFee: shippingFee.toFixed(2),
      formattedPayAmount: payAmount.toFixed(2),
      productAmount: productAmount,
      discountAmount: discountAmount,
      shippingFee: shippingFee,
      payAmount: payAmount
    });
  },

  async loadDefaultAddress() {
    try {
      const result = await getAddressList();
      console.log('获取地址列表结果:', result);
      
      const addressList = result?.addresses || result?.list || [];
      
      if (addressList.length > 0) {
        const defaultAddress = addressList.find(addr => addr.is_default) || addressList[0];
        console.log('选中的默认地址:', defaultAddress);
        this.setData({ selectedAddress: defaultAddress });
      }
    } catch (error) {
      console.error('加载地址失败:', error);
    }
  },

  goToAddressList() {
    const selectedId = this.data.selectedAddress?.id || '';
    wx.navigateTo({
      url: `/pages/address-list/index?select=1&selectedId=${selectedId}`
    });
  },

  toggleCouponPicker() {
    this.setData({ showCouponPicker: !this.data.showCouponPicker });
  },

  selectCoupon(e) {
    const index = e.currentTarget.dataset.index;
    const coupon = this.data.availableCoupons[index];
    
    if (this.data.selectedCoupon && this.data.selectedCoupon.id === coupon.id) {
      this.setData({ 
        selectedCoupon: null,
        showCouponPicker: false
      });
    } else {
      this.setData({ 
        selectedCoupon: coupon,
        showCouponPicker: false
      });
    }
    
    this.updateFormattedAmounts();
  },

  toggleShippingPicker() {
    this.setData({ showShippingPicker: !this.data.showShippingPicker });
  },

  selectShipping(e) {
    const index = e.currentTarget.dataset.index;
    const shipping = this.data.shippingMethods[index];
    
    this.setData({ 
      selectedShipping: shipping,
      showShippingPicker: false
    });
    
    this.updateFormattedAmounts();
    this.calculateEstimatedArrival();
  },

  togglePayMethodPicker() {
    this.setData({ showPayMethodPicker: !this.data.showPayMethodPicker });
  },

  selectPayMethod(e) {
    const index = e.currentTarget.dataset.index;
    const payMethod = this.data.payMethods[index];
    
    this.setData({ 
      selectedPayMethod: payMethod,
      showPayMethodPicker: false
    });
  },

  toggleMoreOptions() {
    this.setData({ showMoreOptions: !this.data.showMoreOptions });
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value });
  },

  decreaseQuantity() {
    if (this.data.quantity > 1) {
      this.setData({ quantity: this.data.quantity - 1 });
      this.updateFormattedAmounts();
      this.loadAvailableCoupons();
    }
  },

  increaseQuantity() {
    const maxQuantity = this.data.product?.stock || 99;
    if (this.data.quantity < maxQuantity) {
      this.setData({ quantity: this.data.quantity + 1 });
      this.updateFormattedAmounts();
      this.loadAvailableCoupons();
    }
  },

  async submitOrder() {
    if (!this.data.selectedAddress) {
      showToast('请选择收货地址');
      return;
    }

    if (this.data.isSubmitting) return;

    this.setData({ isSubmitting: true });
    showLoading('提交订单中...');

    try {
      const product = this.data.product;
      const address = this.data.selectedAddress;
      const selectedCoupon = this.data.selectedCoupon;
      const selectedShipping = this.data.selectedShipping;
      const selectedPayMethod = this.data.selectedPayMethod;

      const orderData = {
        teacher_id: product.teacher_id,
        teacher_user_id: product.teacher_user_id,
        items: [
          {
            product_id: product.id,
            product_title: product.title,
            product_image: product.cover_image || product.images?.[0] || '',
            price: product.price,
            original_price: product.original_price || product.price,
            quantity: this.data.quantity
          }
        ],
        address: {
          name: address.name,
          phone: address.phone,
          province: address.province,
          city: address.city,
          district: address.district,
          detail: address.detail
        },
        remark: this.data.remark,
        shipping_fee: selectedShipping ? selectedShipping.fee : 0,
        shipping_method: selectedShipping ? selectedShipping.key : 'standard',
        pay_method: selectedPayMethod ? selectedPayMethod.key : 'wechat'
      };

      if (selectedCoupon) {
        orderData.user_coupon_id = selectedCoupon.user_coupon_id;
        orderData.coupon_id = selectedCoupon.id;
      }

      console.log('提交订单数据:', orderData);

      const result = await createOrder(orderData);
      console.log('订单创建结果:', result);

      hideLoading();
      showToast('订单创建成功', 'success');

      setTimeout(() => {
        wx.switchTab({
          url: '/pages/orders/index'
        });
      }, 1500);

    } catch (error) {
      console.error('提交订单失败:', error);
      hideLoading();
      showToast(error.message || '提交失败，请重试');
      this.setData({ isSubmitting: false });
    }
  },

  onShow() {
    console.log('订单确认页面显示');
    if (this.data.selectedAddress) {
      console.log('当前选中的地址:', this.data.selectedAddress);
    }
  },

  hideAllPickers() {
    this.setData({
      showCouponPicker: false,
      showShippingPicker: false,
      showPayMethodPicker: false
    });
  }
});
