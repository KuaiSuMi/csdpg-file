package com.example;

/**
 * Inventory service for testing cross-service calls.
 */
public class InventoryService {
    private static final int AVAILABLE_STOCK = 100;

    
    public boolean checkStock(String itemId, int quantity) {
        // Simulate stock check
        return quantity <= AVAILABLE_STOCK;
    }
    
    public void reserveStock(String itemId, int quantity) {
        System.out.println("Reserved " + quantity + " units of " + itemId);
    }
    
    public void releaseStock(String itemId, int quantity) {
        System.out.println("Released " + quantity + " units of " + itemId);
    }
}
