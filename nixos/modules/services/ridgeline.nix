{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.homelab.services.ridgeline;
  identities = config.homelab.serviceIdentities;
in
{
  options.homelab.services.ridgeline = {
    enable = lib.mkEnableOption "Ridgeline — hiking loadout recommender";

    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
      description = "TCP port for the Ridgeline webapp.";
    };

    userUid = lib.mkOption {
      type = lib.types.int;
      default = identities.uids.ridgeline;
      description = "UID for the ridgeline service user.";
    };

    obsidianMount = lib.mkOption {
      type = lib.types.path;
      default = "/mnt/obsidian";
      description = "Read-only mount point for the Obsidian gear vault.";
    };

    stateDir = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/ridgeline";
      description = "Application state directory (SQLite, managed GPX files).";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.ridgeline = {
      uid = cfg.userUid;
      group = "ridgeline";
      home = cfg.stateDir;
      isSystemUser = true;
    };
    users.groups.ridgeline = { };

    environment.systemPackages = with pkgs; [
      # TBD — the app runtime (python + dependencies, or a packaged binary)
      #pkgs.python3
      #pkgs.uv
    ];

    systemd.tmpfiles.rules = [
      "d /var/lib/ridgeline 0750 ridgeline ridgeline -"
      "d /var/lib/ridgeline/state 0750 ridgeline ridgeline -"
      "d /var/lib/ridgeline/gpx 0750 ridgeline ridgeline -"
    ];

    systemd.services.ridgeline = {
      description = "Ridgeline — hiking loadout recommender";
      wantedBy = [ "multi-user.target" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];

      serviceConfig = {
        Type = "simple";
        User = "ridgeline";
        Group = "ridgeline";
        WorkingDirectory = cfg.stateDir;
        ExecStart = ''
          # TBD — replace with the actual app launch command once runtime is decided
          ${pkgs.python3}/bin/python -m http.server ${toString cfg.port}
        '';
        Restart = "on-failure";
        RestartSec = "10s";
        StateDirectory = "ridgeline";
        UMask = "0027";
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [
          "/var/lib/ridgeline"
          "/var/lib/ridgeline/state"
          "/var/lib/ridgeline/gpx"
        ];
        ReadOnlyPaths = [
          cfg.obsidianMount
        ];
      };
    };

    networking.firewall.allowedTCPPorts = [ cfg.port ];
  };
}
