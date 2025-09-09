def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--example", dest="example", type=str, required=False,
                        help="Run file for testing purposes")
    args = parser.parse_args()

    import examples.backend


if __name__ == "__main__":
    main()
