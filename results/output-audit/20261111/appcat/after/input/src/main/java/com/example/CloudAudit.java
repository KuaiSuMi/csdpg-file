package com.example;

public class CloudAudit {
    public String createOrder(String item, int quantity) {
        if (quantity <= 0) throw new IllegalArgumentException("quantity");
        String order = "ORD-" + item + "-" + quantity;
        System.out.println("AUDIT " + order);
        return order;
    }
}
