import com.example.*;

public class ProjectContract {
    static int checks;

    static void check(boolean value) {
        checks++;
        if (!value) throw new AssertionError("Contract check " + checks);
    }

    static class Payment extends PaymentService {
        double charged;
        public String processPayment(double amount) throws PaymentException {
            charged = amount;
            super.processPayment(amount);
            return "fixed";
        }
    }

    static class Inventory extends InventoryService {
        int reserved;
        public void reserveStock(String item, int quantity) { reserved += quantity; }
    }

    public static void main(String[] args) throws Exception {
        int[] quantities = {1, 49, 50, 99, 100};
        double[] expected = {10, 490, 475, 940.5, 900};
        for (int i = 0; i < quantities.length; i++) {
            Payment payment = new Payment();
            Inventory inventory = new Inventory();
            OrderService order = new OrderService(payment, inventory);
            check(order.createOrder("item", 10, quantities[i]).equals("ORD-fixed-item"));
            check(Math.abs(payment.charged - expected[i]) < 0.00001);
            check(inventory.reserved == quantities[i]);
        }
        Payment payment = new Payment();
        Inventory inventory = new Inventory();
        OrderService order = new OrderService(payment, inventory);
        check(order.createOrder("item", 10, 101).equals("OUT_OF_STOCK"));
        check(payment.charged == 0 && inventory.reserved == 0);
        check(order.createOrder("item", 10001, 1).equals("PAYMENT_FAILED"));
        check(inventory.reserved == 0);
        try {
            order.createOrder(null, 10, 1);
            throw new AssertionError("null item accepted");
        } catch (IllegalArgumentException expectedError) { checks++; }
        try {
            order.createOrder("item", 0, 1);
            throw new AssertionError("zero amount accepted");
        } catch (IllegalArgumentException expectedError) { checks++; }
        check(order.getOrderStatus(null).equals("INVALID"));
        check(order.calculateFactorial(0) == 1 && order.calculateFactorial(5) == 120);
        System.out.println("contract_checks=" + checks);
    }
}
