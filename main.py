def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", dest="test", type=str, required=False,
                        help="Run file for testing purposes")
    args = parser.parse_args()

    if args.test is not None:
        try:
            exec(f"import tests.{args.test}")
        except ImportError:
            print(f"There is no {args.test} test file")
        # finally:
        #     exit()
    else:
        pass


if __name__ == "__main__":
    main()
