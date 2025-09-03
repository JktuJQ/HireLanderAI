def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--example", dest="example", type=str, required=False,
                        help="Run file for testing purposes")
    args = parser.parse_args()

    if args.example is not None:
        try:
            exec(f"import examples.{args.example}")
        except ImportError:
            print(f"There is no `examples/{args.example}.py` test file")
        except Exception as e:
            print(e)
        finally:
            exit()
    else:
        pass


if __name__ == "__main__":
    main()
