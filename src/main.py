from openij.client import CanonClient


def main() -> None:
    client = CanonClient("192.168.1.173")

    print("Imprimante configurée :")
    print(client.url)
    print()

    print("Lancement de l'alignement automatique...")

    try:
        result = client.automatic_head_alignment()

    except ConnectionError as error:
        print()
        print(f"Erreur : {error}")
        return

    print()
    print("Commande acceptée par l'imprimante.")
    print(f"Job ID      : {result.job_id}")
    print(f"Opération   : {result.operation}")
    print(f"Réponse     : {result.response}")
    print(f"Progression : {result.progress}")

    print()
    print("Réponse GetStatus complète :")
    print(result.status_xml)


if __name__ == "__main__":
    main()