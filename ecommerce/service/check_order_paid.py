""" check_order_paid service function for ecommerce app """

from django.db import connection
             
def check_order_paid(item_dict):
    """
    Prevent double purchase. If any orders made in the last three hours exist 
    with this item ID, and the fields passed in are identical, then this is a 
    duplicate purchase. This function only checks coupons, not built out to 
    handle multiple products. Returns boolean.
    """
    cursor = connection.cursor() 
    try:
        cursor.execute("""
            SELECT CASE WHEN count(*) > 0 THEN TRUE ELSE FALSE END
            FROM ecommerce_order AS orders
            INNER JOIN ecommerce_orderitem AS orderitem
                ON orders.id = orderitem.order_id
             -- Product determines what table our item is in.
            INNER JOIN ecommerce_product AS product
                ON orderitem.product_id = product.id
            LEFT JOIN ecommerce_payment AS payment
                ON payment.order_id = orders.id
                    AND payment.status = 'A'
            -- Product name identifies this item as coupon.
            INNER JOIN coupon_coupon coupon 
                ON product.name = 'Flyer Placement'
                    AND coupon.id = orderitem.item_id
            WHERE coupon.id = %s
            -- purchase made when payment is Approved 
            -- or if total is 0 (free purchase)
            AND (payment.status = 'A' OR (
                    payment.status is null AND total = 0)) 
            -- Interval adds a unit and by unit type to a datetime value.
            -- In this case subtracts 3 hours from the current time.
            AND (COALESCE(payment.create_datetime, orders.create_datetime) > 
                now() + interval '-3 hour')
            AND coupon.offer_id = %s
            AND is_valid_monday = %s
            AND is_valid_tuesday = %s
            AND is_valid_wednesday = %s
            AND is_valid_thursday = %s
            AND is_valid_friday = %s
            AND is_valid_saturday = %s
            AND is_valid_sunday = %s
            AND start_date = %s
            AND expiration_date = %s
            AND is_redeemed_by_sms = %s
            AND site_id = %s
            AND product_id = %s
            AND total = %s 
            AND custom_restrictions = %s
            LIMIT 1;""", 
            [item_dict['coupon_id'], 
            int(item_dict['offer_id']), 
            bool(item_dict['is_valid_monday']), 
            bool(item_dict['is_valid_tuesday']), 
            bool(item_dict['is_valid_wednesday']), 
            bool(item_dict['is_valid_thursday']), 
            bool(item_dict['is_valid_friday']), 
            bool(item_dict['is_valid_saturday']), 
            bool(item_dict['is_valid_sunday']), 
            item_dict['start_date'], 
            item_dict['expiration_date'], 
            bool(item_dict['is_redeemed_by_sms']), 
            item_dict['site_id'], 
            item_dict['product_id'], 
            item_dict['total'], 
            item_dict['custom_restrictions']])
        return cursor.fetchone()[0]
    except KeyError:
        return False
    
