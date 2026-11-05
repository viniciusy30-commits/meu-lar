package android.content.res;
public class AssetManager {
    public String root;
    public AssetManager(String r) { root = r; }
    public java.io.InputStream open(String p) throws java.io.IOException { return new java.io.FileInputStream(root + "/" + p); }
}
