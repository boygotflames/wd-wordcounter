fn main() {
    println!("cargo:rerun-if-changed=src/main.rs");
    
    // Build configuration
    if cfg!(target_os = "windows") {
        println!("cargo:rustc-link-arg=/DEBUG:NONE");
        println!("cargo:rustc-link-arg=/OPT:REF");
        println!("cargo:rustc-link-arg=/OPT:ICF");
    }
}