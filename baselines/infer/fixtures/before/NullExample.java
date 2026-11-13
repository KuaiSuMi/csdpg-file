public class NullExample {
    static int size(String value) {
        return value.length();
    }

    public static void main(String[] args) {
        System.out.println(size(null));
    }
}
