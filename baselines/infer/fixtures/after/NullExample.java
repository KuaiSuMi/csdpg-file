public class NullExample {
    static int size(String value) {
        return value == null ? 0 : value.length();
    }

    public static void main(String[] args) {
        System.out.println(size(null));
    }
}
