{
  ...
}:

{
  networking.hostName = "ridgeline";
  networking.defaultGateway = "10.10.10.1";

  networking.interfaces.eth0.ipv4.addresses = [
    {
      address = "10.10.10.TBD";
      prefixLength = 24;
    }
  ];

  homelab.services.ridgeline = {
    enable = true;
    # port = 8080;            # default
    # obsidianMount = "/mnt/obsidian";  # default
    # stateDir = "/var/lib/ridgeline";  # default
  };

  homelab.services.beszelAgent = {
    enable = true;
  };
}
