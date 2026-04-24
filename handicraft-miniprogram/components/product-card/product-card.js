Component({
  properties: {
    product: {
      type: Object,
      value: {}
    },
    showTeacher: {
      type: Boolean,
      value: false
    },
    showSales: {
      type: Boolean,
      value: true
    }
  },

  data: {},

  methods: {
    onCardTap() {
      const { product } = this.properties;
      this.triggerEvent('cardtap', { product });
    },

    onTeacherTap(e) {
      e.stopPropagation();
      const { product } = this.properties;
      this.triggerEvent('teachertap', { teacherId: product.teacherId });
    },

    onFavoriteTap(e) {
      e.stopPropagation();
      const { product } = this.properties;
      this.triggerEvent('favoritetap', { 
        productId: product.id,
        isFavorite: product.isFavorite 
      });
    }
  }
});
