{
  description = "Provides containers + caddy configuration to run danielnaylor.uk";

  inputs = {
    docker-tools.url = "github:Danie-1/docker-tools-flake";
  };

  outputs = { ... }: {
    nixosModules.default = { config, lib, ... }: with config.danielnaylor-uk; {
      options.danielnaylor-uk = with lib; with types; {
        blue-port = mkOption { type = str; default = "5101"; };
        green-port = mkOption { type = str; default = "5102"; };
        active = mkOption { type = enum [ "blue" "green" ]; default = "blue"; };
        url = mkOption { type = str; default = "danielnaylor.uk"; };
        aliases = mkOption { type = listOf str; default = [ "danielnaylor.co.uk" "notes.ggim.me" "dn410.ggim.me" ]; };
        root-folder = mkOption { type = str; default = "/home/daniel/Documents/projects/dn410_server/"; };
        notes-folder = mkOption { type = str; default = "${root-folder}/notes"; };
        docker-data-folder = mkOption { type = str; default = "${root-folder}/docker-data"; };
        docker-network = mkOption { type = str; default = "danielnayloruk"; };
        openFirewall = mkOption { type = bool; default = true; };
        active-port = mkOption { type = str; default = if config.danielnaylor-uk.active == "blue" then blue-port else green-port; };
      };
      config = lib.mkMerge [
        {
          services.caddy = {
            enable = true;
            virtualHosts = {
              "${url}" = {
                extraConfig = ''
                  reverse_proxy 127.0.0.1:${active-port} {
                    header_up Host {host}
                    header_up X-Real-IP {remote_ip}
                  }
                '';
              };
            } // lib.optionalAttrs (aliases != []) {
              "${builtins.head aliases}" = {
                serverAliases = builtins.tail aliases;
                extraConfig = ''
                  redir https://${url}
                '';
              };
            };
          };
          docker-tools.networks = [ "${docker-network}" ];
          virtualisation.oci-containers.containers."danielnayloruk-reindex" = {
            image = "ghcr.io/danie-1/danielnaylor.uk";
            volumes = [
              "${notes-folder}:/base_folder:rw"
            ];
            cmd = [ "uv" "run" "python" "index_htmls.py" ];
            dependsOn = [
              "danielnayloruk-search"
            ];
            extraOptions = [
              "--network-alias=reindex"
              "--network=${docker-network}"
            ];
          };
          virtualisation.oci-containers.containers."danielnayloruk-search" = {
            image = "ghcr.io/danie-1/sonic";
            volumes = [
              "${docker-data-folder}/sonic:/usr/src/sonic/data:rw"
            ];
            extraOptions = [
              "--network-alias=search"
              "--network=${docker-network}"
            ];
          };
          virtualisation.oci-containers.containers."danielnayloruk-site" = {
            image = "ghcr.io/danie-1/danielnaylor.uk";
            volumes = [
              "${notes-folder}:/base_folder:rw"
            ];
            ports = [
              "127.0.0.1:${active-port}:8000"
            ];
            dependsOn = [
              "danielnayloruk-search"
            ];
            extraOptions = [
              "--network-alias=site"
              "--network=${docker-network}"
            ];
          };
        }
        (lib.mkIf openFirewall {
            networking.firewall.allowedTCPPorts = [ 80 443 ];
        })
      ];
    };
  };
}
