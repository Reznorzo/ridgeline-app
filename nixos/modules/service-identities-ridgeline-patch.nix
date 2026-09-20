{ lib, ... }:

{
  options.homelab.serviceIdentities = {
    groups.media.gid = lib.mkOption {
      type = lib.types.int;
      default = 2000;
      description = "Shared group ID for services that need controlled access to media paths.";
    };

    uids = {
      sonarr = lib.mkOption { type = lib.types.int; default = 2001; description = "UID for the Sonarr service user."; };
      radarr = lib.mkOption { type = lib.types.int; default = 2002; description = "UID for the Radarr service user."; };
      lidarr = lib.mkOption { type = lib.types.int; default = 2003; description = "UID for the Lidarr service user."; };
      bazarr = lib.mkOption { type = lib.types.int; default = 2004; description = "UID for the Bazarr service user."; };
      jellyfin = lib.mkOption { type = lib.types.int; default = 2010; description = "UID for the Jellyfin service user."; };
      beszelHub = lib.mkOption { type = lib.types.int; default = 2101; description = "UID for the Beszel hub service user."; };
      hermes = lib.mkOption { type = lib.types.int; default = 2201; description = "UID for the Hermes service user."; };
      ridgeline = lib.mkOption { type = lib.types.int; default = 2300; description = "UID for the Ridgeline service user."; };
    };
  };
}
