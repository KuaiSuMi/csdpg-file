import com.example.CloudAudit;

public class Contract {
    public static void main(String[] args) throws Exception {
        CloudAudit service = new CloudAudit();
        if (!service.createOrder("book", 2).equals("ORD-book-2")) {
            throw new AssertionError("order result changed");
        }
        try {
            service.createOrder("book", 0);
            throw new AssertionError("invalid quantity accepted");
        } catch (IllegalArgumentException expected) {
            System.out.println("CONTRACT_OK:2");
        }
    }
}
