fn main() {
    let addr = app_lib::start_server();
    println!("Rust server listening on http://{}", addr);
    loop {
        std::thread::park();
    }
}
