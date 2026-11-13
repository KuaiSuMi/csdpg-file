package com.example;

import java.io.FileWriter;
import java.io.IOException;

public class CloudAudit {
    public String createOrder(String item, int quantity) throws IOException {
        if (quantity <= 0) throw new IllegalArgumentException("quantity");
        String order = "ORD-" + item + "-" + quantity;
        try (FileWriter audit = new FileWriter("orders.log", true)) {
            audit.write("AUDIT " + order + System.lineSeparator());
        }
        return order;
    }
}
